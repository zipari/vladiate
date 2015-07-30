# Vladiate

## Description
Vladiate helps you write explicit assertions for every field of your CSV file.

## Features
* **Write validation schemas in plain-old Python**

  No UI, no XML, no JSON, just code.

* **Write your own validators**

  Vladiate comes with a few by default, but there's no reason you can't write
  your own.

* **Validate multiple files at once**

  Either with the same schema, or different ones.

## Documentation
### Installation
Installing:

    $ pip install vladiate

### Quickstart
Below is an example of a `vladfile.py`

```python
from vladiate import Vlad
from vladiate.validators import UniqueValidator, SetValidator
from vladiate.inputs import LocalFile

class YourFirstValidator(Vlad):
    source = LocalFile('vampires.csv')
    validators = {
        'Column A': [
            UniqueValidator()
        ],
        'Column B': [
            SetValidator(['Vampire', 'Not A Vampire'])
        ]
    }
```

Here we define a number of validators for a local file `vampires.csv`,
which would look like this:

    Column A,Column B
    Vlad the Impaler,Not A Vampire
    Dracula,Vampire
    Count Chocula,Vampire

We then run `vladiate` in the same directory as your `.csv` file:

    $ vladiate

And get the following output:

    Validating YourFirstValidator(source=LocalFile('vampires.csv'))
    Passed! :)

#### Handling Changes
Let's imagine that you've gotten a new CSV file, `potential_vampires.csv`, that
looks like this:

    Column A,Column B
    Vlad the Impaler,Not A Vampire
    Dracula,Vampire
    Count Chocula,Vampire
    Ronald Reagan,Maybe A Vampire

If we were to update our first validator to use this file as follows:

    - class YourFirstValidator(Vlad):
    -     source = LocalFile('vampires.csv')
    + class YourFirstFailingValidator(Vlad):
    +     source = LocalFile('potential_vampires.csv')

we would get the following error:

    Validating YourFirstValidator(source=LocalFile('potential_vampires.csv'))
    Failed :(
      SetValidator failed 1 time(s) on field: 'Column B'
        Invalid fields: ['Maybe A Vampire']

And we would know that we'd either need to sanitize this field, or add it to the
`SetValidator`.

#### Starting from scratch
To make writing a new `vladfile.py` easy, Vladiate will give meaningful error
messages.

Given the following as `real_vampires.csv`:

    Column A,Column B,Column C
    Vlad the Impaler,Not A Vampire
    Dracula,Vampire
    Count Chocula,Vampire
    Ronald Reagan,Maybe A Vampire

We could write a bare-bones validator as follows:

```python
class YourFirstEmptyValidator(Vlad):
    source = LocalFile('real_vampires.csv')
    validators = {}
```

Running this with `vladiate` would give the following error:

    Validating YourFirstEmptyValidator(source=LocalFile('real_vampires.csv'))
    Missing...
      Missing validators for:
        'Column A': [],
        'Column B': [],
        'Column C': [],

Vladiate expects something to be specified for every column, *even if it is an
empty list* (more on this later). We can easily copy and paste from the error
into our `vladfile.py` to make it:

```python
class YourFirstEmptyValidator(Vlad):
    source = LocalFile('real_vampires.csv')
    validators = {
        'Column A': [],
        'Column B': [],
        'Column C': [],
    }
```

When we run _this_ with `vladiate`, we get:

    Validating YourSecondEmptyValidator(source=LocalFile('real_vampires.csv'))
    Failed :(
      EmptyValidator failed 4 time(s) on field: 'Column A'
        Invalid fields: ['Dracula', 'Vlad the Impaler', 'Count Chocula', 'Ronald Reagan']
      EmptyValidator failed 4 time(s) on field: 'Column B'
        Invalid fields: ['Maybe A Vampire', 'Not A Vampire', 'Vampire']
      EmptyValidator failed 4 time(s) on field: 'Column C'
        Invalid fields: ['Real', 'Not Real']

This is because Vladiate interprets an empty list of validators for a field as
an `EmptyValidator`, which expects an empty string in every field. This helps us
make meaningful decisions when adding validators to our `vladfile.py`. It also
ensures that we are not forgetting about a column or field which is not empty.

#### Built-in Validators
Vladiate comes with a few common validators built-in:

* _class_ `Validator`

  Generic validator. Should be subclassed by any custom validators. Not to be
  used directly.

* _class_ `CastValidator`

  Generic "can-be-cast-to-x" validator. Should be subclassed by any cast-test
  validator. Not to be used directly.

* _class_ `IntValidator`

  Validates whether a field can be cast to an `int` type or not.

  * `empty_ok=False`

    Specify whether a field which is an empty string should be ignored.

* _class_ `FloatValidator`

  Validates whether a field can be cast to an `float` type or not.

  * `empty_ok=False`

    Specify whether a field which is an empty string should be ignored.

* _class_ `SetValidator`

  Validates whether a field is in the specified set of possible fields.

  * `valid_set=[]`

    List of valid possible fields

  * `empty_ok=False`

    Implicity adds the empty string to the specified set.

* _class_ `UniqueValidator`

  Ensures that a given field is not repeated in any other column. Can
  optionally determine "uniqueness" with other fields in the row as well via
  `unique_with`.

  * `unique_with=[]`

    List of field names to make the primary field unique with.

* _class_ `EmptyValidator`

  Ensure that a field is always empty. Essentially the same as an empty
  `SetValidator`. This is used by default when a field has no validators.

* _class_ `Ignore`

  Always passes validation. Used to explicity ignore a given column.

### Testing
To run the tests

    python setup.py test

## Authors
* [Dustin Ingram](https://github.com/di)

## License
Open source MIT license.
