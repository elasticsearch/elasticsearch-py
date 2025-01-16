#  Licensed to Elasticsearch B.V. under one or more contributor
#  license agreements. See the NOTICE file distributed with
#  this work for additional information regarding copyright
#  ownership. Elasticsearch B.V. licenses this file to you under
#  the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
# 	http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing,
#  software distributed under the License is distributed on an
#  "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
#  KIND, either express or implied.  See the License for the
#  specific language governing permissions and limitations
#  under the License.

from datetime import date, datetime
from fnmatch import fnmatch
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    get_args,
    overload,
)

try:
    from types import UnionType
except ImportError:
    UnionType = None  # type: ignore

from typing_extensions import dataclass_transform

from .exceptions import ValidationException
from .field import Binary, Boolean, Date, Field, Float, Integer, Nested, Object, Text
from .mapping import Mapping
from .utils import DOC_META_FIELDS, ObjectBase

if TYPE_CHECKING:
    from elastic_transport import ObjectApiResponse

    from .index_base import IndexBase


class MetaField:
    def __init__(self, *args: Any, **kwargs: Any):
        self.args, self.kwargs = args, kwargs


class InstrumentedField:
    """Proxy object for a mapped document field.

    An object of this instance is returned when a field is accessed as a class
    attribute of a ``Document`` or ``InnerDoc`` subclass. These objects can
    be used in any situation in which a reference to a field is required, such
    as when specifying sort options in a search::

        class MyDocument(Document):
            name: str

        s = MyDocument.search()
        s = s.sort(-MyDocument.name)  # sort by name in descending order
    """

    def __init__(self, name: str, field: Field):
        self._name = name
        self._field = field

    # note that the return value type here assumes classes will only be used to
    # access fields (I haven't found a way to make this type dynamic based on a
    # decision taken at runtime)
    def __getattr__(self, attr: str) -> "InstrumentedField":
        try:
            # first let's see if this is an attribute of this object
            return super().__getattribute__(attr)  # type: ignore
        except AttributeError:
            try:
                # next we see if we have a sub-field with this name
                return InstrumentedField(f"{self._name}.{attr}", self._field[attr])
            except KeyError:
                # lastly we let the wrapped field resolve this attribute
                return getattr(self._field, attr)  # type: ignore

    def __pos__(self) -> str:
        """Return the field name representation for ascending sort order"""
        return f"{self._name}"

    def __neg__(self) -> str:
        """Return the field name representation for descending sort order"""
        return f"-{self._name}"

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"InstrumentedField[{self._name}]"


class DocumentMeta(type):
    _doc_type: "DocumentOptions"
    _index: "IndexBase"

    def __new__(
        cls, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]
    ) -> "DocumentMeta":
        # DocumentMeta filters attrs in place
        attrs["_doc_type"] = DocumentOptions(name, bases, attrs)
        return super().__new__(cls, name, bases, attrs)

    def __getattr__(cls, attr: str) -> Any:
        if attr in cls._doc_type.mapping:
            return InstrumentedField(attr, cls._doc_type.mapping[attr])
        return super().__getattribute__(attr)


class DocumentOptions:
    type_annotation_map = {
        int: (Integer, {}),
        float: (Float, {}),
        bool: (Boolean, {}),
        str: (Text, {}),
        bytes: (Binary, {}),
        datetime: (Date, {}),
        date: (Date, {"format": "yyyy-MM-dd"}),
    }

    def __init__(self, name: str, bases: Tuple[type, ...], attrs: Dict[str, Any]):
        meta = attrs.pop("Meta", None)

        # create the mapping instance
        self.mapping: Mapping = getattr(meta, "mapping", Mapping())

        # register the document's fields, which can be given in a few formats:
        #
        # class MyDocument(Document):
        #     # required field using native typing
        #     # (str, int, float, bool, datetime, date)
        #     field1: str
        #
        #     # optional field using native typing
        #     field2: Optional[datetime]
        #
        #     # array field using native typing
        #     field3: list[int]
        #
        #     # sub-object, same as Object(MyInnerDoc)
        #     field4: MyInnerDoc
        #
        #     # nested sub-objects, same as Nested(MyInnerDoc)
        #     field5: list[MyInnerDoc]
        #
        #     # use typing, but override with any stock or custom field
        #     field6: bool = MyCustomField()
        #
        #     # best mypy and pyright support and dataclass-like behavior
        #     field7: M[date]
        #     field8: M[str] = mapped_field(MyCustomText(), default="foo")
        #
        #     # legacy format without Python typing
        #     field9 = Text()
        #
        #     # ignore attributes
        #     field10: ClassVar[string] = "a regular class variable"
        annotations = attrs.get("__annotations__", {})
        fields = set([n for n in attrs if isinstance(attrs[n], Field)])
        fields.update(annotations.keys())
        field_defaults = {}
        for name in fields:
            value: Any = None
            required = None
            multi = None
            if name in annotations:
                # the field has a type annotation, so next we try to figure out
                # what field type we can use
                type_ = annotations[name]
                skip = False
                required = True
                multi = False
                while hasattr(type_, "__origin__"):
                    if type_.__origin__ == ClassVar:
                        skip = True
                        break
                    elif type_.__origin__ == Mapped:
                        # M[type] -> extract the wrapped type
                        type_ = type_.__args__[0]
                    elif type_.__origin__ == Union:
                        if len(type_.__args__) == 2 and type_.__args__[1] is type(None):
                            # Optional[type] -> mark instance as optional
                            required = False
                            type_ = type_.__args__[0]
                        else:
                            raise TypeError("Unsupported union")
                    elif type_.__origin__ in [list, List]:
                        # List[type] -> mark instance as multi
                        multi = True
                        required = False
                        type_ = type_.__args__[0]
                    else:
                        break
                if skip or type_ == ClassVar:
                    # skip ClassVar attributes
                    continue
                if type(type_) is UnionType:
                    # a union given with the pipe syntax
                    args = get_args(type_)
                    if len(args) == 2 and args[1] is type(None):
                        required = False
                        type_ = type_.__args__[0]
                    else:
                        raise TypeError("Unsupported union")
                field = None
                field_args: List[Any] = []
                field_kwargs: Dict[str, Any] = {}
                if isinstance(type_, type) and issubclass(type_, InnerDoc):
                    # object or nested field
                    field = Nested if multi else Object
                    field_args = [type_]
                elif type_ in self.type_annotation_map:
                    # use best field type for the type hint provided
                    field, field_kwargs = self.type_annotation_map[type_]  # type: ignore

                if field:
                    field_kwargs = {
                        "multi": multi,
                        "required": required,
                        **field_kwargs,
                    }
                    value = field(*field_args, **field_kwargs)

            if name in attrs:
                # this field has a right-side value, which can be field
                # instance on its own or wrapped with mapped_field()
                attr_value = attrs[name]
                if isinstance(attr_value, dict):
                    # the mapped_field() wrapper function was used so we need
                    # to look for the field instance and also record any
                    # dataclass-style defaults
                    attr_value = attrs[name].get("_field")
                    default_value = attrs[name].get("default") or attrs[name].get(
                        "default_factory"
                    )
                    if default_value:
                        field_defaults[name] = default_value
                if attr_value:
                    value = attr_value
                    if required is not None:
                        value._required = required
                    if multi is not None:
                        value._multi = multi

            if value is None:
                raise TypeError(f"Cannot map field {name}")

            self.mapping.field(name, value)
            if name in attrs:
                del attrs[name]

        # store dataclass-style defaults for ObjectBase.__init__ to assign
        attrs["_defaults"] = field_defaults

        # add all the mappings for meta fields
        for name in dir(meta):
            if isinstance(getattr(meta, name, None), MetaField):
                params = getattr(meta, name)
                self.mapping.meta(name, *params.args, **params.kwargs)

        # document inheritance - include the fields from parents' mappings
        for b in bases:
            if hasattr(b, "_doc_type") and hasattr(b._doc_type, "mapping"):
                self.mapping.update(b._doc_type.mapping, update_only=True)

    @property
    def name(self) -> str:
        return self.mapping.properties.name


_FieldType = TypeVar("_FieldType")


class Mapped(Generic[_FieldType]):
    """Class that represents the type of a mapped field.

    This class can be used as an optional wrapper on a field type to help type
    checkers assign the correct type when the field is used as a class
    attribute.

    Consider the following definitions::

        class MyDocument(Document):
            first: str
            second: M[str]

        mydoc = MyDocument(first="1", second="2")

    Type checkers have no trouble inferring the type of both ``mydoc.first``
    and ``mydoc.second`` as ``str``, but while ``MyDocument.first`` will be
    incorrectly typed as ``str``, ``MyDocument.second`` should be assigned the
    correct ``InstrumentedField`` type.
    """

    __slots__: Dict[str, Any] = {}

    if TYPE_CHECKING:

        @overload
        def __get__(self, instance: None, owner: Any) -> InstrumentedField: ...

        @overload
        def __get__(self, instance: object, owner: Any) -> _FieldType: ...

        def __get__(
            self, instance: Optional[object], owner: Any
        ) -> Union[InstrumentedField, _FieldType]: ...

        def __set__(self, instance: Optional[object], value: _FieldType) -> None: ...

        def __delete__(self, instance: Any) -> None: ...


M = Mapped


def mapped_field(
    field: Optional[Field] = None,
    *,
    init: bool = True,
    default: Any = None,
    default_factory: Optional[Callable[[], Any]] = None,
    **kwargs: Any,
) -> Any:
    """Construct a field using dataclass behaviors

    This function can be used in the right side of a document field definition
    as a wrapper for the field instance or as a way to provide dataclass-compatible
    options.

    :param field: The instance of ``Field`` to use for this field. If not provided,
    an instance that is appropriate for the type given to the field is used.
    :param init: a value of ``True`` adds this field to the constructor, and a
    value of ``False`` omits it from it. The default is ``True``.
    :param default: a default value to use for this field when one is not provided
    explicitly.
    :param default_factory: a callable that returns a default value for the field,
    when one isn't provided explicitly. Only one of ``factory`` and
    ``default_factory`` can be used.
    """
    return {
        "_field": field,
        "init": init,
        "default": default,
        "default_factory": default_factory,
        **kwargs,
    }


@dataclass_transform(field_specifiers=(mapped_field,))
class InnerDoc(ObjectBase, metaclass=DocumentMeta):
    """
    Common class for inner documents like Object or Nested
    """

    @classmethod
    def from_es(
        cls,
        data: Union[Dict[str, Any], "ObjectApiResponse[Any]"],
        data_only: bool = False,
    ) -> "InnerDoc":
        if data_only:
            data = {"_source": data}
        return super().from_es(data)


class DocumentBase(ObjectBase):
    """
    Model-like class for persisting documents in elasticsearch.
    """

    @classmethod
    def _matches(cls, hit: Dict[str, Any]) -> bool:
        if cls._index._name is None:
            return True
        return fnmatch(hit.get("_index", ""), cls._index._name)

    @classmethod
    def _default_index(cls, index: Optional[str] = None) -> str:
        return index or cls._index._name

    def _get_index(
        self, index: Optional[str] = None, required: bool = True
    ) -> Optional[str]:
        if index is None:
            index = getattr(self.meta, "index", None)
        if index is None:
            index = getattr(self._index, "_name", None)
        if index is None and required:
            raise ValidationException("No index")
        if index and "*" in index:
            raise ValidationException("You cannot write to a wildcard index.")
        return index

    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(
                f"{key}={getattr(self.meta, key)!r}"
                for key in ("index", "id")
                if key in self.meta
            ),
        )

    def to_dict(self, include_meta: bool = False, skip_empty: bool = True) -> Dict[str, Any]:  # type: ignore[override]
        """
        Serialize the instance into a dictionary so that it can be saved in elasticsearch.

        :arg include_meta: if set to ``True`` will include all the metadata
            (``_index``, ``_id`` etc). Otherwise just the document's
            data is serialized. This is useful when passing multiple instances into
            ``elasticsearch.helpers.bulk``.
        :arg skip_empty: if set to ``False`` will cause empty values (``None``,
            ``[]``, ``{}``) to be left on the document. Those values will be
            stripped out otherwise as they make no difference in elasticsearch.
        """
        d = super().to_dict(skip_empty=skip_empty)
        if not include_meta:
            return d

        meta = {"_" + k: self.meta[k] for k in DOC_META_FIELDS if k in self.meta}

        # in case of to_dict include the index unlike save/update/delete
        index = self._get_index(required=False)
        if index is not None:
            meta["_index"] = index

        meta["_source"] = d
        return meta
