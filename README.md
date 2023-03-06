```

 ██╗███████╗███████╗ █████╗ ██╗     ██╗
██╔╝██╔════╝██╔════╝██╔══██╗██║     ╚██╗
██║ ███████╗█████╗  ███████║██║      ██║
██║ ╚════██║██╔══╝  ██╔══██║██║      ██║
╚██╗███████║███████╗██║  ██║███████╗██╔╝
 ╚═╝╚══════╝╚══════╝╚═╝  ╚═╝╚══════╝╚═╝

          (teal makes sense)
```

## Write meaningful teal in s-expressions!

SEAL is a minimlistic language with its powerful cross-compiler designed to simplify the process of writing Algorand TEAL programs using s-expressions. With SEAL, developers can write TEAL programs in a more readable and efficient way, making it accessible to both beginners and experienced developers alike. SEAL is built to take advantage of the easy-to-read nature of s-expressions, which makes it even easier to write and read TEAL programs. This tool is perfect for anyone looking to develop on the Algorand blockchain and write smart contracts in an efficient and streamlined way.

SEAL does not add any additional layers of abstraction to the TEAL language. By building upon the existing foundations of TEAL and leveraging the readability and simplicity of s-expressions, SEAL provides a unique and innovative way of writing TEAL programs that is accessible to developers of all levels of experience. SEAL is designed to preserve the core functionality and "opcodes" of TEAL, while making it easier to read, write, and deploy programs on the Algorand blockchain. With SEAL, developers can benefit from a more streamlined and efficient workflow, without sacrificing the power and flexibility of TEAL. If you're looking for a tool that makes writing TEAL programs more accessible and easier than ever before, then SEAL is the perfect choice.

See a minimal example below to experience how SEAL enhances the readability and ease-of-use of TEAL:

```typescript
($MAX_SIZE 10) `This is a constant, name all capitalized`

($i 0) `Variable assignment`

`While loop using reading and incrementing $i`
(@while (< $i $MAX_SIZE)
    ($i (+ $i 1))
)
```

Simply compile your seal code to convert it to a valid TEAL language.

```bash
% seal compile demo.seal > demo.teal
```

Our `seal` code will be compiled into a perfectly valid, well organized `teal` file.

```teal
#pragma version 8
int 0
store 0 // $i
while_0:
load 0 // $i
int 10 // $MAX_SIZE
<
bz while_0_end
load 0 // $i
int 1
+
store 0 // $i
b while_0
while_0_end:
```

You're now perfectly ready to deploy and test out your newly created smart contract.

```bash
% sandbox copyTo demo.teal
>>> Now copying demo.teal to Algod container

% sandbox goal app create [...] --approval-prog demo.teal
>>> Created app with app index 1

% sandbox goal app optin [...] --app-id 1
>>> Transaction committed!

% sandbox goal app call [...] --app-id 1 --app-arg 'str:visit'
>>> Transaction committed!

% sandbox goal app read [...] --app-id 1 --local
>>> {
>>>   "visits": {
>>>     "tt": 2,
>>>     "ui": 1
>>>   }
>>> }
```

## Installation

To get started with SEAL, simply follow the installation instructions below and once installed, you can start writing TEAL programs in s-expressions and use SEAL to convert them into TEAL bytecode that can be deployed to the Algorand blockchain.

```bash
% pip install seal-lang
```

## Usage

Cli tool can be accessed simply typing `seal` in your commmand prompt where you can find basic usage info prompted.

```bash
% seal
>>> usage: seal [-h] [-v] {compile,spec} ...
>>>
>>> positional arguments:
>>>   {compile,spec}
>>>
>>> options:
>>>   -h, --help      show this help message and exit
>>>   -v, --version   show program's version number and exit
```

`compile` subcommand is also as follows, please note the `strict` option to
enable strict compiler checks. More information will be available soon.

```
% seal compile --help
>>> usage: seal compile [-h] [-p PRAGMA_VERSION] [-s] path
>>>
>>> positional arguments:
>>>   path
>>>
>>> optional arguments:
>>>   -h, --help         show this help message and exit
>>>   -p PRAGMA_VERSION  pragma version
>>>   -s                 strict mode
```

## Documenation

Seal simplifies the process of writing smart contracts in Algorand's teal language by providing a more concise syntax for managing the stack. With seal, you can use embedded s-expressions to define and manipulate the stack in a more intuitive way. This makes it easier to write and maintain complex smart contracts.

For example, consider the following code in original teal:

```teal
int 1
int 2
+
int 3
+
```

This code pushes the values 1 and 2 onto the stack, adds them together, pushes the value 3 onto the stack, and adds it to the previous result. Using seal, you could write the same code more concisely like this:

```typescript
(+ 1 2 3)
```

This code uses the + operator to add the values 1, 2, and 3 together, which are all pushed onto the stack automatically. As you can see, seal greatly simplifies the process of writing Algorand smart contracts by providing a more intuitive syntax for stack management.

### Opcodes

In Seal, any sequence of characters that is not a special syntax element (such as those starting with $ or @) will be treated as a Teal opcode. Teal opcodes are the basic building blocks of Teal programs, and are used to perform various operations on the program's state and data.

Here's a simple demonstration of how opcodes are called in Seal:

```typescript
err;
```

Compiles into:

```teal
err
```

If any opcode requires stack arguments, you can construct your opcode call using s-expression syntax to manage the stack. For example:

```typescript
(assert (== 5 (+ 3 2)))
```

Compiles into:

```teal
int 5
int 3
int 2
+
==
assert
```

You can chain and nest several opcodes using the lisp-style syntax to create more complex operations.

### Fields & Immediate Args

In Algorand, some opcodes like `global`, `txn`, `txna`, `gtxn`, `itxn_field` and several others behave like namespaces for accessing various transactional and global data in a smart contract. Also there are many other opcodes like `substring` accepting immediate arguments such as `start` and `end` to adjust the behaviour of regarding opcode rather than stack arguments.

Seal provides a specific syntax known as dot notation allowing developers to access fields within these namespaces using the format `namespace.field1.field2`. For example, `txn.ApplicationID` accesses the `ApplicationID` field within the `txn` namespace. Or to call `substring` accompanied with immediate args like `substring.3.5`.

Please find below to find out how dot notation is used to achieve specific use cases:

```typescript
(== txna.ApplicationArgs.0 (substring.0.5 "Hello World"))
```

Compiles into:

```teal
txna ApplicationArgs 0
byte "Hello World"
substring 0 5
==
```

### Labels

Labels in Teal are named markers that allow the program to "jump" to a specific point in the code. In "Seal" they are defined in similar way by using the syntax `labelname:` where labelname can be any valid identifier. Labels are commonly used with branching opcodes like `b`, `bz`, `bnz`, and many more, which allow the program to change the order of execution based on the instruction.

Here you may find a demonstration on how to use labels in "Seal":

```typescript
(@case
    (== txna.ApplicationArgs.0 "foo")
    b.foo
)
err

(foo:
    (assert
        (== txna.ApplicationArgs.1 "bar")
    )
)
err
```

Compiles into:

```teal
txna ApplicationArgs 0
byte "foo"
==
bz case_0
b foo
case_0:
err
foo:
txna ApplicationArgs 1
byte "bar"
==
assert
err
```

### Comments

In Seal, comments are used to document the code and improve its readability. A comment in Seal starts with a backtick symbol \` and ends with another backtick symbol \`. Everything between these two symbols is ignored by the compiler and does not emit any Teal code. Here's an example:

```typescript
`This is a single-line comment`;
```

You can also write multi-line comments in Seal by using the backtick symbol multiple times. Here's an example:

```typescript
`
This is a
multi-line
comment
`;
```

It's important to note that comments should be used sparingly and only when necessary to explain the code's purpose or implementation. Overuse of comments can make the code harder to read and maintain.

### Literals

Literals in "seal" are used to represent values of integers and bytes. Integers are compiled to TEAL's `int` opcode, which pushes a 64-bit unsigned integer value onto the TEAL stack, while bytes are compiled to TEAL's `byte` opcode, which pushes a byte string value onto the TEAL stack.

Literals can be used in expressions, assigned to variables, and passed as function arguments. For example:

```typescript
42;
("Hello World");
```

Compiles into:

```teal
int 42
byte "Hello World"
```

### Constants

Constants in "seal" are defined using all capitalized names starting with a `$` sign, like `$MAX_SIZE`. Constant definitions do not emit any code by themselves. Instead, when a constant is referred to using `$CONSTANT_NAME`, the value of the constant is substituted into the literal expression they hold.

For example:

```typescript
($MAX_SIZE 42)
($MESSAGE "Hello, World!")
($TRUE 1)

$MAX_SIZE
$MESSAGE
$TRUE
```

Compiles into:

```teal
int 42 // $MAX_SIZE
byte "Hello, World!" // $MESSAGE
int 1 // $TRUE
```

### Variables

Variables in "seal" are defined using names starting with a lower case letter and a `$` sign, like `$my_var`. When a variable is defined, the value of the assigned expression is stored in the scratch space, using an auto-incremented index to denote where it's saved. Variables can be used in expressions, assigned new values, and passed as function arguments.

To refer to a variable, use its name starting with a `$` sign. The compiled code will then load the value from scratch space by using the indexed value.

For example:

```typescript
($my_var 42)
($another_var "Hello, World!")

$my_var
$another_var
```

Compiles into:

```teal
int 42
store 0 // $my_var

byte "Hello, World!"
store 1 // $another_var

load 0 // $my_var
load 1 // $another_var
```

Please note that the use of variables in "seal" is limited by the scratch space available in Algorand's TEAL language. TEAL has a maximum scratch space size of 256 bytes, which limits the number of variables that can be used in a smart contract. It is important to carefully manage the use of variables and their associated memory usage to ensure that your smart contract stays within the limits of the TEAL language.

### Conditions

Conditions in "seal" are used for making decisions based on certain conditions. There are two types of conditions: single conditions and compound conditions.

#### Single Conditions

Single conditions are constructed using the `@case` operator. The @case operator takes its first expression as the test value and the second expression as the action to take if the test is true. For example:

```typescript
(@case
    (== $my_var "Hello World")
    (return 1)
)
```

This condition will return 1 if the value of the variable `$my_var` is equal to "Hello World".

#### Compound Conditions

Compound conditions are constructed using the `@in` operator. The `@in` operator expects all of its children to be `@case` statements and works exactly like "if .. else if .. else" conditions. For example:

```typescript
(@in
    (@case (== $my_var "Hello World") (return 1))
    (@case (== $my_var "Goodbye World") (return 2))
    (return 3)
)
```

This condition will check the value of the variable `$my_var` against the first `@case` statement, and if it's true, it will return `1`. If it's not true, it will check the second `@case` statement, and so on. If none of the `@case` statements are true, it will return `3`.

#### Inner Transactions

"Seal" introduces the `#itxn` command as a shorthand for inner transactions in Algorand TEAL. The `#itxn` command encapsulates the functionality of `itxn_begin` and `itxn_submit` statements, making it easier for developers to express inner transactions in their smart contracts. With `#itxn`, developers can use `itxn_field` to set any attribute of the inner transaction and commit it eventually.

```typescript
(@itxn
    (itxn_field.AssetAmount 1000)
    (itxn_field.XferAsset txna.Assets.0)
    (itxn_field.AssetReceiver txn.Sender)
    (itxn_field.TypeEnum int.axfer)
)
```

Compiles into:

```teal
itxn_begin
txna Assets 0
itxn_field XferAsset
txn Sender
itxn_field AssetReceiver
int axfer
itxn_field TypeEnum
itxn_submit
```

## Disclaimer

Please note that SEAL is currently in the early stages of development and while not tested it thoroughly, it may still contain bugs or errors. As such, use SEAL with caution, and always test your programs thoroughly before deploying them to the Algorand blockchain.

This software cannot be held responsible for any errors or issues that may arise from the use of it.

If you encounter any problems or have any questions about SEAL, please don't hesitate to reach out or raise an issue.
Your support and feedback is very much appreciated.

## Licence

Copyright (c) 2023 Kadir Pekel.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the 'Software'), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
