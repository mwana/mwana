#-------------------------------------------------------------------------------
# Name:        py_cupom
# Purpose:     generate shorter case insensitive alphanumeric ids from integers
#
# Author:      Paulo Scardine
#
# Created:     09/09/2010
# Copyright:   (c) Paulo Scardine 2010
# Licence:     GNU GPL
#-------------------------------------------------------------------------------
#!/usr/bin/env python

"""
This module was created to generate short alphanumeric ids for a discount coupon
application. It can also be useful to generate shared session keys for games and
any other application where you need an easy to share alphanumeric code.

It can be used as a short hash for integers, but in fact is uses a base 32
notation that has the following attributes:

    * Collision-free 1 to 1 mapping for positive integers
    * Somewhat compact: encodes 5 bit per digit
    * Generates a case insensitive code
    * Pads to a given number of digits
    * Does not use 'L'/'l', 'I'/'i' and 'O','o' to avoid mistakes with 0/1.
    * Optional Luhn mod N algorithm included for checksum digit

Maximum range can be calculated as 32 elevated to the number of digits used.

You can customize FW_MAP and BW_MAP to make codes harder to guess, but this
algorithm was not designed to be crypto safe. In my map I made 0=A because
I prefer AAAY1 over 000Y1 when padding. This has some side-effects:

   * AAAAA1 == AAA1 == 1 (000001 == 0001 == 1)
   * checksum calculation also ignores any A(s) on the left

Sorry, guys, only Python >= 2.6 for now. Backporting python 2.6+ bin() is left
as an exercise to the reader.
"""

import math

FW_MAP = {
    # 0=A because I prefer AAAY1 over 000Y1 when padding
    # Side-effects:
    #   * AAAAA == AAA == A (00000 == 000 == 0)
    #   * checksum ignores any A(s) on the left side
    '00000':	'A',
    '00001':	'1',
    '00010':	'2',
    '00011':	'3',
    '00100':	'4',
    '00101':	'5',
    '00110':	'6',
    '00111':	'7',
    '01000':	'8',
    '01001':	'9',
    '01010':	'0',
    '01011':	'B',
    '01100':	'C',
    '01101':	'D',
    '01110':	'E',
    '01111':	'F',
    '10000':	'G',
    '10001':	'H',
    '10010':	'J',
    '10011':	'K',
    '10100':	'M',
    '10101':	'N',
    '10110':	'P',
    '10111':	'Q',
    '11000':	'R',
    '11001':	'S',
    '11010':	'T',
    '11011':	'V',
    '11100':	'W',
    '11101':	'X',
    '11110':	'Y',
    '11111':	'Z',
}

BW_MAP = {
    'A': '00000', 'a': '00000',
    '1': '00001', 'i': '00001', 'I': '00001', 'l': '00001', 'L': '00001',
    '2': '00010',
    '3': '00011',
    '4': '00100',
    '5': '00101',
    '6': '00110',
    '7': '00111',
    '8': '01000',
    '9': '01001',
    '0': '01010', 'O': '01010', 'o': '01010',
    'B': '01011', 'b': '01011',
    'C': '01100', 'c': '01100',
    'D': '01101', 'd': '01101',
    'E': '01110', 'e': '01110',
    'F': '01111', 'f': '01111',
    'G': '10000', 'g': '10000',
    'H': '10001', 'h': '10001',
    'J': '10010', 'j': '10010',
    'K': '10011', 'k': '10011',
    'M': '10100', 'm': '10100',
    'N': '10101', 'n': '10101',
    'P': '10110', 'p': '10110',
    'Q': '10111', 'q': '10111',
    'R': '11000', 'r': '11000',
    'S': '11001', 's': '11001',
    'T': '11010', 't': '11010',
    'V': '11011', 'v': '11011',
    'W': '11100', 'w': '11100',
    'X': '11101', 'x': '11101',
    'Y': '11110', 'y': '11110',
    'Z': '11111', 'z': '11111',
}

def digit(code):
    """Generate Luhn mod N checksum digit"""
    factor = 2
    total = 0
    n = len(FW_MAP)
    for l in code[::-1]:
        code_point = int(BW_MAP[l], 2)
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        addend = (addend / n) + (addend % n)
        total += addend
    remainder = total % n
    check_code_point = n - remainder
    check_code_point = check_code_point % n
    return FW_MAP[bin(check_code_point)[2:].rjust(5, '0')]

def check(code):
    """Checks Luhn mod N code+digit for validity"""
    factor = 1
    total = 0
    n = len(FW_MAP)
    for l in code[::-1]:
        code_point = int(BW_MAP[l], 2)
        addend = factor * code_point
        factor = 1 if factor == 2 else 2
        addend = (addend / n) + (addend % n)
        total += addend
    remainder = total % n
    return remainder == 0

def encode(n, length=None, check_digit=False):
    """Encode integer to base 32 shorter case insensitive alphanumeric code.

Parameters:
    digits: pads result to 'length' digits
    check_digit: appends Luhn mod N check digit if True (default=False).
    """
    n = abs(n) # positive integers only
    if length:
        length = int(length)
        if int(n) > 32**length:
            raise OverflowError('%d bigger than 32**%d' % (n, length))
    else:
        length = int(math.ceil(math.log(int(n), 32)))
    # Map binary string to base 32
    padded_bin = bin(n)[2:].rjust(5*length,'0')
    code = ''.join([ FW_MAP[padded_bin[i*5:i*5+5]] for i in range(0, length) ])
    return code + digit(code) if check_digit else code

def decode(s, check_digit=False):
    """Decodes an alphanumeric code to integer"""
    if check_digit:
        if not check(s):
            raise ChecksumError("'%s' is invalid cs digit for '%s'" % (s[-1:], s[:-1]))
        s = s[:-1]
    return int(''.join([BW_MAP[l] for l in str(s)]), 2)

class ChecksumError(Exception):
    pass

def main():
    print """Use 'import py_cupom' inside your code."""

if __name__ == '__main__':
    main()
