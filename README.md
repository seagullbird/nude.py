# nude.py

Automatic **nudity** detect.

## Usage

```zsh
$ python3 nude.py nude_pic1.jpg nude_pic2.jpg
```

## Options

**-r**: Reduce image size to increase speed of scanning

**-v**: Generating areas of skin image

## Example

There are 9 examples in `test_case/` folder. Try any and enjoy.

**test_case/0.jpg:**

 ![0](test_case/6.jpg)

```
$ python3 nude.py -v test_case/6.jpg
```

Output:

```
True test_case/6.jpg None 706×1000: result=True message='Nude!!'
```

**test_case/0_Nude.jpg:**

 ![0_Nude](test_case/6_Nude.jpg)

