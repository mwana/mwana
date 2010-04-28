"""
Provides utilities to cleanup text
"""
NUMBER_DICTIONARY = {
0 :'Zero'
, 1: "One"
, 2: "Two"
, 3: "Three"
, 4: "Four"
, 5: "Five"
, 6: "Six"
, 7: "Seven"
, 8: "Eight"
, 9: "Nine"
, 10: "Ten"
, 11: "Eleven"
, 12: "Twelve"
, 13: "Thirteen"
, 14: "Fourteen"
, 15: "Fifteen"
, 16: "Sixteen"
, 17: "Seventeen"
, 18: "Eighteen"
, 19: "Nineteen"
, 20: "Twenty"
, 30: "Thirty"
, 40: "Forty"
, 50: "Fifty"
, 60: "Sixty"
, 70: "Seventy"
, 80: "Eighty"
, 90: "Ninety"
, 'Zero': 0
, 'One': 1
, 'Two': 2
, 'Three': 3
, 'Four': 4
, 'Five': 5
, 'Six': 6
, 'Seven': 7
, 'Eight': 8
, 'Nine': 9
, 'Ten': 10
, 'Eleven': 11
, 'Leven': 11
, 'Twelve': 12
, 'Thirteen': 13
, 'Fourteen': 14
, 'Forteen': 14
, 'Fifteen': 15
, 'Sixteen': 16
, 'Seventeen': 17
, 'Eighteen': 18
, 'Nineteen': 19
, 'Twenty': 20
, 'Thirty': 30
, 'Forty': 40
, 'Fourty': 40
, 'Foty': 40
, 'Fifty': 50
, 'Sixty': 60
, 'Seventy': 70
, 'Eighty': 80
, 'Ninety': 90
, 'Ninty': 90
}

PLACE_VALUE = {
'Hundred':100
, 'Thousand':1000
, 'Million':1000000
}

DIGIT_FOR_LETTER = {'i': '1', 'l': '1', 'o': '0', 'I':'1', 'O':'0',
'0':'0',
'1':'1',
'2':'2',
'3':'3',
'4':'4',
'5':'5',
'6':'6',
'7':'7',
'8':'8',
'9':'9'
}

class InputCleaner:
    def soundex(self, name, len=4):
        name = str(name)#make sure its a string--Trevor
        """ soundex module conforming to Knuth's algorithm
            implementation 2000-12-24 by Gregory Jorgensen
            public domain
        """

        # digits holds the soundex values for the alphabet
        digits = '01230120022455012623010202'
        sndx = ''
        fc = ''

        # translate alpha chars in name to soundex digits
        for c in name.upper():
            if c.isalpha():
                if not fc: fc = c   # remember first letter
                d = digits[ord(c)-ord('A')]
                # duplicate consecutive soundex digits are skipped
                if not sndx or (d != sndx[-1]):
                    sndx += d

        # replace first digit with first alpha character
        sndx = fc + sndx[1:]

        # remove all 0s from the soundex code
        sndx = sndx.replace('0', '')

        # return soundex code padded to len characters
        return (sndx + (len * '0'))[:len]

    def remove_double_spaces(self, text):
        """
        return text with double spaces removed from input text
        """
        while "  " in text:
            text = text.replace("  ", " ")
        return text

    def digit_to_word(self, digit):
        """
        Returns a word representation of the number for a limited set of digits
        """
        try:
            return NUMBER_DICTIONARY[digit]
        except KeyError:
            return None


    def words_to_digits(self, text):
        """
        Returns integer representation of numbers entered as words
        """
        if not text.strip():
            return None
        text = text.title().replace(" And", "")
        text = self.remove_double_spaces(text)
        tokens = text.strip().title().split(" ")
        #correct tokens
        for i in range(len(tokens)):
            found = False
            for key in NUMBER_DICTIONARY.keys():
                if tokens[i] not in NUMBER_DICTIONARY.keys():
                    if self.soundex(tokens[i]) == self.soundex(key):
                        tokens[i] = key
                        found = True
                        break
            if not found:
                for key in PLACE_VALUE.keys():
                    if tokens[i] not in PLACE_VALUE.keys():
                        if self.soundex(tokens[i]) == self.soundex(key):
                            tokens[i] = key
                            break

        if not tokens:
            return None
        try:
            if len(tokens) == 2:
                if tokens[0].title() == 'Hundred' or self.soundex(tokens[0]) == self.soundex('Hundred'):
                    return 100 + int(NUMBER_DICTIONARY[tokens[1]])
                elif tokens[1].title() in PLACE_VALUE.keys():
                    return int(NUMBER_DICTIONARY[tokens[0]]) * int(PLACE_VALUE[tokens[1]])
                else:
                    return int(NUMBER_DICTIONARY[tokens[0]]) + int(NUMBER_DICTIONARY[tokens[1]])
            elif len(tokens) == 1:
                return int(NUMBER_DICTIONARY[tokens[0]])
            elif len(tokens) == 3:
                if tokens[0].title() == 'Hundred':
                    return 100 + int(NUMBER_DICTIONARY[tokens[1]]) + int(NUMBER_DICTIONARY[tokens[2]])
                elif tokens[1].title() == 'Hundred':
                    return int(NUMBER_DICTIONARY[tokens[0]]) * 100 + int(NUMBER_DICTIONARY[tokens[2]])
                elif tokens[1].title() == 'Thousand':
                    return int(NUMBER_DICTIONARY[tokens[0]]) * 1000 + int(NUMBER_DICTIONARY[tokens[2]])
            elif len(tokens) == 4:
                if tokens[2].title() == 'Hundred':
                    return int(NUMBER_DICTIONARY[tokens[0]]) * 100 + int(NUMBER_DICTIONARY[tokens[2]]) + int(NUMBER_DICTIONARY[tokens[3]])
                elif tokens[3].title() == 'Hundred':
                    return int(NUMBER_DICTIONARY[tokens[0]]) * 1000 + int(NUMBER_DICTIONARY[tokens[2]]) * 100
                elif tokens[1].title() == 'Thousand':
                    return int(NUMBER_DICTIONARY[tokens[0]]) * 1000 + int(NUMBER_DICTIONARY[tokens[2]]) + int(NUMBER_DICTIONARY[tokens[3]])
                elif tokens[2].title() == 'Thousand':
                    return (int(NUMBER_DICTIONARY[tokens[0]]) + int(NUMBER_DICTIONARY[tokens[1]])) * 1000 + int(NUMBER_DICTIONARY[tokens[3]])
            elif len(tokens) > 4:
                #I don't want deal with large numbers. db samples are in ones and tens
                return None
        except:
            return None


    def try_replace_oil_with_011(self, str):
        original = str
        result = ''
        """returns string with every occurence of i,I,l,o, and O replaced with 1 or 0 as appropriate"""
        try:
            for char in original:
                result = result + DIGIT_FOR_LETTER[char]
        except KeyError:
            return original
        return result

