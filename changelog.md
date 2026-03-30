# Changelog

All notable changes to Zonetic are documented here.
Versions are listed from newest to oldest.

---

## v0.1.1 — *The Function Update*
> Zonetic gets functions — the most significant feature addition since v0.1.0

**Language**
- `func` keyword and `func form` added — functions are now a first-class construct
- `return` statement added — exits a function and produces its value
- `-> type` explicit return type required on every function — including `-> void` for no return
- `void` type added — exclusively for function return types
- Parameters require explicit mutability — `mut` or `inmut` always declared
- Parameters always passed by copy — changes inside never affect the original outside
- Default parameter values supported — optional at call site
- `func main` as optional program entry point — if present, execution starts there regardless of declaration order
- Pre-scan phase added — all functions registered before execution begins, enabling forward references
- Recursion supported — each call creates an independent `CallFrame` with its own scope
- Functions see the global scope — variables declared outside any function are visible inside all functions

**Call Expression**
- Positional parameters — values matched left to right
- Keyparams — parameters passed by name using `name=value`
- Mixed calls supported — positional first, keyparams after; once a keyparam is used all following must be keyparams
- Keyparam terminology adopted — `param` for positional, `keyparam` for named

**Terminology**
- `parameter` adopted as the single term for both declaration and call contexts
- `keyparam` introduced for parameters passed by name in a call expression
- `argument` retired from Zonetic terminology to avoid confusion

**New Parser Errors**
- `E2013` — missing function name after `func`
- `E2014` — missing `(` after function name
- `E2015` — missing `=` after keyparam name in call
- `E2016` — missing `mut` or `inmut` to start a parameter
- `E2017` — missing parameter name after mutability keyword
- `E2018` — `void` used in invalid context
- `E2019` — invalid type in parameter declaration
- `E2020` — missing `:` after parameter name
- `E2021` — missing `->` after parameter list
- `E2022` — invalid return type after `->`
- `E2023` — keyparam passed more than once in the same call
- `E2024` — positional parameter found after a keyparam
- `E2025` — missing `,` or `)` after parameter (replaces E2015 for unclosed parameter lists)
- `E2026` — `return` found outside any block expr

**New Lexer Errors**
- `E0008` — malformed identifier starting with a digit

**New Semantic Errors**
- `E3013` — Existing function name being used for a new function
- `E3014` — `return` found in some block expr but not in function context
- `E3015` — The return type of the expression that has a `return` found in a function does not match the return type of that function.
- `E3016` — A value(`inmut`) is initialized in a loop when the value is not in the scope of the loop but at least one above it.
- `E3017` — An attempt is being made to declare a function within a function.
- `E3018` — `give` is used in a block that is not valid for expressions, for example: `func`
- `E3019` — semantic detects that there is no `return` in all possible paths (this only applies to functions that do not `return` `void`)
- `E3020` — It's called a non-existent function
- `E3021` — Parameters are added to a function call that the function does not need (if it has zero declared parameters).
- `E3022` — Parameters are being passed that do not match the declared parameters of the function.
- `E3023` — A keyparam is passed with the name of a parameter not declared in the function.
- `E3024` — Passing a value twice to a function parameter causes a collision; only one value can be passed per parameter.
- `E3025` — It was necessary to pass parameters in the call that the function expects
- `E3026` — A function call that returns `void` is used as an expression

**New Semantic Warnings**
- `W3005` — unreachable code below `return`
- `W3006` — unreachable code below `continue` or `break`

**New Runtime Errors**
- `E4002` — Stack Overflow

**Zon Std Lib Mininum**
- `print` print string on screen
- `readInt` — takes a string as an argument and returns a int
- `readFloat` — takes a string as an argument and returns a float
- `readString` — takes a string as an argument and returns a string

---

> **Coming next — v0.1.2: The Struct Update**  
> Basic structs without methods, field declaration and access, and the first modules of the Zonetic standard library for the tree-walker version.

---

## v0.1.0 — *The First Release*
> Tree-walker interpreter complete — first fully functional version of Zonetic

**Interpreter**
- Full rewrite of the interpreter with visitor pattern
- `RuntimeScope` and `RuntimeValue` — clean separation from semantic scope
- All native expressions evaluated — arithmetic, boolean, comparison, unary
- Short-circuit evaluation for `and` and `or`
- `if form` as statement and as expression
- `while form` and `infinity form` with full loop execution
- `break` and `continue` via signal system (`BreakSignal`, `ContinueSignal`)
- `give` statement via `GiveSignal` — exits block and returns value
- Block expressions evaluated in both statement and value context
- `print` statement — concatenates multiple values without separator
- `input` statement — reads user input and converts to target type
- Runtime error system — `ZoneticRuntimeError` bubbles to pipeline entry point

**Runtime Errors**
- `E4001` — division by zero for `/` and `%`

**Semantic** *(completed this version)*
- `if form` as expression — type concordance across all branches
- `else` required when `if form` is used as expression (`E3010`)
- Return type mismatch across branches (`E3011`)
- `give` outside block expression (`E2012`)
- `break` and `continue` outside loop (`E3012`)
- Condition field type warnings — `W3002`, `W3003`
- Infinite loop detection without `break` — `W3004`

---

## v0.0.9
> The Great Refactor Update — language renamed from **Akon** to **Zonetic**

This is the biggest and most important update to date. Nearly everything was rewritten from scratch.

**Language & Identity**
- Language renamed from **Akon** to **Zonetic**
- `zon-cli` replaces `akon-cli`
- Zonny mascot added to the error system

**Lexer**
- Full rewrite with span system
- Binary search index for exact line and column reporting
- `FileMap` for source location tracking

**Normalizer**
- Full rewrite with hybrid statement terminator
- Supports both `;` and newline as statement terminators (one per script)

**Parser**
- Full rewrite with new AST hierarchy — `NodeStmt` and `NodeExpr`
- Real mutability system with `mut` and `inmut`
- Explicit type annotation with `: type` or `UNKNOWN` for future inference
- Form concept introduced — `if form`, `while form`, `infinity form`
- `give` statement for block expressions
- Operator enums — `ADD`, `SUB`, `MUL`, `FDIV`, `IDIV`, `MOD`, `POW`, etc.
- Type enums — `INT`, `FLOAT`, `BOOL`, `STRING`, `UNKNOWN`
- Basic scope system with parent chain

**Diagnostic System** *(new)*
- Indexed error codes — `E####` for errors, `W####` for warnings
- Span-aware error reporting with source line, column pointer, and context
- Severity system — `ERROR` and `WARNING`
- Error registry — all errors defined as data, not hardcoded strings
- Error limit system with summary of remaining errors
- Repeated error condensing — full detail on first occurrence, compact on repeats
- Chronological error sorting by source position
- Zonny — the compiler mascot with personality-driven help messages

**Semantic** *(in progress)*
- Type checker for all native expressions
- Real mutability enforcement
- Type inference from first assignment
- Block expression validation with `give`
- Unreachable code detection after `give`
- Scope chain with `Symbol` entries

**Documentation** *(all created in this version)*
- [`NERT`](docs/expressions/NERT.md), [`precedence_doc`](docs/expressions/precedence.md), [`forms_doc`](docs/forms/forms_doc.md), [`condition_field_doc`](docs/forms/condition_field_doc.md)
- [`types_doc`](docs/others/types_doc.md), [`expression_doc`](docs/expressions/expression_doc.md), [`statements_doc`](docs/statements/statements_doc.md), [`variable_vs_value_doc`](docs/others/variable_vs_value_doc.md)
- [`declaration_stmt_doc`](docs/statements/declaration_stmt_doc.md), [`assignment_stmt_doc`](docs/statements/assignment_stmt_doc.md), [`give_stmt_doc`](docs/statements/give_stmt_doc.md)
- [`break_stmt_doc`](docs/statements//break_stmt_doc.md), [`continue_stmt_doc`](docs/statements//continue_stmt_doc.md)

> Interpreter rewrite pending — will complete this version.

---

## v0.0.8
> The Semantic Prototype

- Semantic analysis added — type checker for all existing expressions and statements

---

## v0.0.7
> The Normalizer Update

- `TheNormalizer` added — hybrid statement terminator, supports both `;` and newline
- `NEWLINE` token added to the lexer
- Parser fix — precedence of `and`, `or`, and `not` corrected

---

## v0.0.6
> The Loop Update

- `while` loop added
- `loop` sugar syntax added (now called `infinity`)
- `break` and `continue` statements added
- `True` and `False` keywords changed to `true` and `false`
- Lexer refactor

---

## v0.0.5
> The CLI Update

- `akon-cli` added (now `zon-cli`) with REPL support
- Parentheses no longer required for conditions

---

## v0.0.4
> The Assignment Update

- Compound and standard assignment operators added: `=`, `+=`, `-=`, `*=`, `**=`, `/=`, `%=`
- General structure improvements

---

## v0.0.3
> The Control Flow Update

- `if`, `elif`, `else` added

---

## v0.0.2
> The Operators Update

- Arithmetic operators: `+`, `-`, `*`, `**`, `/`, `%`
- Comparison operators: `<`, `>`, `<=`, `>=`, `==`, `!=`
- Boolean operators: `and`, `or`, `not`

---

## v0.0.1
> The Beginning — language was called **Akon** at this point

- Lexer, tokens, and `TokenType`
- Basic AST nodes
- Basic parser
- Basic environment
- Basic interpreter
- `AkonErrors` — first error system (now replaced)
