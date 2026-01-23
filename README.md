# dict2dc - dictionary to dataclass parsing

`dict2dc` is a small Python library that helps to parse Python dicts to dataclass structures.
E.g., these dicts could originate from JSON deserialization.

The library supports nested dataclasses, collections and union types.
It always tries to initiate the best matching class.
