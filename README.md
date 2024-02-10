# Lambda Calculus Interpreter
This is an interpreter for lambda calculus operations. It supports the main features from the lambda calculus framework, from abstraction and application to creation and use of variables and complex macros (that store full expressions or operators). The interpreter will show the initial AST of the expression, apply any beta reductions or alpha conversions necessary and output the resulting expression.

## Requirements

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install the required python packages:

```bash
pip install antlr4-tools
pip install antlr4-python-runtime
```

## Execution

Firstly, we must generate the parser, lexer and visitor from the language grammar in lc.g4. To do so we run the following command which compiles the antlr4 grammar:

```bash
antlr4 -Dlanguage=Python3 -no-listener -visitor lc.g4
```

Secondly, we run the actual program. This interpreter has two versions. A CLI-based one and a second one which runs on a telegram bot.

To run the CLI interpreter, we run the `lc.py` file like so:

```bash
python3 lc.py
```

For the telegram bot, we run the `achurch.py` file like so:

```bash
python3 achurch.py
```

## Valid Operations

### Terms

Looking at the grammar we can see that this interpret supports terms as inputs. The following inputs are considered valid terms:

- A variable, defined by any of the alphabet letters (from a to z) in underscore.
- An abstraction, defined by a symbol 'λ' or '\' followed by a set of one or more variables, a '.' as a separator and, finally, a term that acts as the body of the abstraction (i.e: λxyz.abc is an abstraction of the variables x, y and z over the body "abc"). 
- An application, defined by 2 terms written back to back. For example, (λx.y)z is an application of the variable z (which is considered the argument) to the abstraction λx.y (which is considered the function).
 
Note: Any term can be parenthesized to define precisely the order of operations desired.

#### Macros

Additionally, it supports the creation and use of macros. Macros are defined via an assignment with the following syntax:

A macro name followed by a symbol '=' or '≡' followed by a term.

The macro name has to follow these principles:
- For normal macros: An uppercase alphabetical character followed by more uppercase letters or numbers (i.e: "N0T3" is a valid macro name whereas "Note" or "3NOT" are not)
- For operators: Any non-alphabetical symbol (such as, but not limited to "%", "+" and "&")
