# lang

Interpreter for my own language

## features 

- functions
- closures
- recursion
- builtin io
- repl
- coercion

## usage

run with python
```bash
python3 main.py <input_file>
```

## showcase

```
fun make_countdown(end_msg)
    fun count(n)
        if n <= 0
            print(end_msg)
        else
            print(n)
            count(n - 1)
        end
    end
    return count
end

run = make_countdown("countdown finished")
time = 3
while time
    run(time)
    time -= 1
end
```

output of this example:
```
3
2
1
countdown finished
2
1
countdown finished
1
countdown finished
```

## todo

- arrays
- libraries