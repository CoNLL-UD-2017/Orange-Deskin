#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
import sys

sys.stdout = codecs.getwriter('utf-8')(sys.stdout)


LATCYR = {
    "А": "A",
    "а": "a",

    "Б": "B",
    "б": "b",

    "В": "V",
    "в": "v",

    "Г": "G",
    "г": "g",

    "Д": "D",
    "д": "d",

    "Ђ": "Đ",
    "ђ": "đ",

    "Е": "E",
    "е": "e",

    "Ж": "Ž",
    "ж": "ž",

    "З": "Z",
    "з": "z",

    "И": "I",
    "и": "i",

    "Ј": "J",
    "ј": "j",

    "К": "K",
    "к": "k",

    "Л": "L",
    "л": "l",

    "Љ": "Lj",
    "љ": "lj",

    "М": "M",
    "м": "m",

    "Н": "N",
    "н": "n",

    "Њ": "Nj",
    "њ": "nj",

    "О": "O",
    "о": "o",

    "П": "P",
    "п": "p",

    "Р": "R",
    "р": "r",

    "С": "S",
    "с": "s",

    "Т": "T",
    "т": "t",

    "Ћ": "Ć",
    "ћ": "ć",

    "У": "U",
    "у": "u",

    "Ф": "F",
    "ф": "f",

    "Х": "H",
    "х": "h",

    "Ц": "C",
    "ц": "c",

    "Ч": "Č",
    "ч": "č",

    "Џ": "Dž",
    "џ": "dž",

    "Ш": "Š",
    "ш": "š"
}

class SR2HR:
    def __init__(self, inf, outf):
        ifp = codecs.open(inf, "r", encoding="utf-8")
        ofp = codecs.open(outf, "w", encoding="utf-8")

        latcyrU = {}
        for cyr,lat in LATCYR.items():
            cyru = unicode(cyr, "utf-8")
            latu = unicode(lat, "utf-8")
            latcyrU[cyru] = latu
        

	for line in ifp:
            for cyr,lat in latcyrU.items():
                line = line.replace(cyr,lat)
            ofp.write(line)
    
	ifp.close()
	ofp.close()



if __name__ == "__main__":
    sh = SR2HR(sys.argv[1], sys.argv[2])
    
        
