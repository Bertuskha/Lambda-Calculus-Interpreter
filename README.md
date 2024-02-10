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

## CLI Runtime

Executing `lc.py` will open a text prompt to input lambda terms or macro definitions and in turn proper output will be shown (the operations done by the interpreted as well as the resulting term). Here are some examples of execution (the lines with `?` symbols are inputs and the rest are output messages):

Operation with both alpha conversions and beta reductions:
```
? (λyx.y)x
Arbre:
((λy.(λx.y))x)
α-conversió: x → z
(λy.(λx.y)) → (λy.(λz.y))
β-reducció:
((λy.(λz.y))x) → (λz.x)
Resultat:
(λz.x)
```

Infinite recursive operation(there's a maximum step count of 50 to ensure program termination):
```
? (λx.(xx))(λx.(xx))
Arbre:
((λx.(xx))(λx.(xx)))
β-reducció:
((λx.(xx))(λx.(xx))) → ((λx.(xx))(λx.(xx)))
β-reducció:
((λx.(xx))(λx.(xx))) → ((λx.(xx))(λx.(xx)))
β-reducció:
((λx.(xx))(λx.(xx))) → ((λx.(xx))(λx.(xx)))
...
Resultat:
Nothing
```
Macros example with boolean operations
```
? TRUE≡λx.λy.x
TRUE ≡ (λx.(λy.x))
? FALSE≡λx.λy.y
TRUE ≡ (λx.(λy.x))
FALSE ≡ (λx.(λy.y))
? NOT≡λa.a(λb.λc.c)(λd.λe.d)
TRUE ≡ (λx.(λy.x))
FALSE ≡ (λx.(λy.y))
NOT ≡ (λa.((a(λb.(λc.c)))(λd.(λe.d))))
? NOT TRUE
Arbre:
((λa.((a(λb.(λc.c)))(λd.(λe.d))))(λx.(λy.x)))
β-reducció:
((λa.((a(λb.(λc.c)))(λd.(λe.d))))(λx.(λy.x))) → (((λx.(λy.x))(λb.(λc.c)))(λd.(λe.d)))
β-reducció:
((λx.(λy.x))(λb.(λc.c))) → (λy.(λb.(λc.c)))
β-reducció:
((λy.(λb.(λc.c)))(λd.(λe.d))) → (λb.(λc.c))
Resultat:
(λb.(λc.c))

? NOT FALSE
Arbre:
((λa.((a(λb.(λc.c)))(λd.(λe.d))))(λx.(λy.y)))
β-reducció:
((λa.((a(λb.(λc.c)))(λd.(λe.d))))(λx.(λy.y))) → (((λx.(λy.y))(λb.(λc.c)))(λd.(λe.d)))
β-reducció:
((λx.(λy.y))(λb.(λc.c))) → (λy.y)
β-reducció:
((λy.y)(λd.(λe.d))) → (λd.(λe.d))
Resultat:
(λd.(λe.d))
```
Macros example with arithmetic operations (with infix operators too)
```
? N2≡λs.λz.s(s(z))
N2 ≡ (λs.(λz.(s(sz))))
? N3≡λs.λz.s(s(s(z)))
N2 ≡ (λs.(λz.(s(sz))))
N3 ≡ (λs.(λz.(s(s(sz)))))
? +≡λp.λq.λx.λy.(px(qxy))
N2 ≡ (λs.(λz.(s(sz))))
N3 ≡ (λs.(λz.(s(s(sz)))))
+ ≡ (λp.(λq.(λx.(λy.((px)((qx)y))))))
? N2+N3
Arbre:
(((λp.(λq.(λx.(λy.((px)((qx)y))))))(λs.(λz.(s(sz)))))(λs.(λz.(s(s(sz))))))
β-reducció:
((λp.(λq.(λx.(λy.((px)((qx)y))))))(λs.(λz.(s(sz))))) → (λq.(λx.(λy.(((λs.(λz.(s(sz))))x)((qx)y)))))
β-reducció:
((λq.(λx.(λy.(((λs.(λz.(s(sz))))x)((qx)y)))))(λs.(λz.(s(s(sz)))))) → (λx.(λy.(((λs.(λz.(s(sz))))x)(((λs.(λz.(s(s(sz)))))x)y))))
β-reducció:
((λs.(λz.(s(sz))))x) → (λz.(x(xz)))
β-reducció:
((λz.(x(xz)))(((λs.(λz.(s(s(sz)))))x)y)) → (x(x(((λs.(λz.(s(s(sz)))))x)y)))
β-reducció:
((λs.(λz.(s(s(sz)))))x) → (λz.(x(x(xz))))
β-reducció:
((λz.(x(x(xz))))y) → (x(x(xy)))
Resultat:
(λx.(λy.(x(x(x(x(xy)))))))
```
