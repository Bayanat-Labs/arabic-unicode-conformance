# Copyright 2026 Bayanat Labs
# SPDX-License-Identifier: CC-BY-4.0
"""Source of the suite's test cases (data, CC BY 4.0). Every input below was written for this suite; no text is
taken from a corpus or from another project's tests. scripts/build_suite.py turns this list into cases/*.jsonl.

C(category, input, rationale, level="must", lang="ar", keep="", x=None)
  keep  code points (as a string of characters) that raw-safe-v1, bayanat-norm-v1 and asr-eval-v1 must keep
  x     expectations stated explicitly from the policy text, keyed r (raw-safe-v1), b (bayanat-norm-v1),
        a (asr-eval-v1), c (nfc), k (nfkc); the build fails when the reference implementation disagrees
B(category, hex_bytes, rationale)  an input given as raw bytes that are not valid UTF-8 (every policy rejects it)
"""

CASES = []


def C(category, text, rationale, level="must", lang="ar", keep="", x=None):
    CASES.append({"category": category, "input": text, "rationale_en": rationale, "level": level,
                  "language_tag": lang, "keep": keep, "x": x or {}, "kind": "text"})


def B(category, hexbytes, rationale, level="must"):
    CASES.append({"category": category, "input_bytes": bytes.fromhex(hexbytes), "rationale_en": rationale,
                  "level": level, "language_tag": "und", "keep": "", "x": {}, "kind": "utf8_bytes"})


# Names for invisible characters and combining marks, so that every case shows its exact code points.
TATWEEL = "ـ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
FATHA, DAMMA, KASRA, SHADDA, SUKUN = "َ", "ُ", "ِ", "ّ", "ْ"
MADDA, HAMZA_A, HAMZA_B, SUPALEF = "ٓ", "ٔ", "ٕ", "ٰ"
ZWSP, ZWNJ, ZWJ, BOM = "​", "‌", "‍", "﻿"
LRM, RLM, ALM = "‎", "‏", "؜"
LRE, RLE, PDF, LRO, RLO = "‪", "‫", "‬", "‭", "‮"
LRI, RLI, FSI, PDI = "⁦", "⁧", "⁨", "⁩"
NBSP, NNBSP, THIN = " ", " ", " "

# ------------------------------------------------------------------------------------------------ tatweel (14)
C("tatweel", "جمـــيل", "Three tatweels inside a word: removed by bayanat-norm-v1 and asr-eval-v1, kept by raw-safe-v1 and by NFC/NFKC (tatweel has no decomposition).",
  x={"r": "جمـــيل", "b": "جميل", "a": "جميل", "k": "جمـــيل"})
C("tatweel", "كـتاب", "One tatweel after the first letter.", x={"b": "كتاب", "r": "كـتاب"})
C("tatweel", "ك" + TATWEEL + FATHA + "تب", "A fatha written on the tatweel: removing the tatweel must not leave a mark without a base in the normalised output.",
  x={"b": "كتب", "r": "ك" + TATWEEL + FATHA + "تب"})
C("tatweel", "ك" + FATHA + TATWEEL + "تب", "Fatha on the letter, then tatweel.", x={"b": "كتب"})
C("tatweel", TATWEEL + "بيت", "Tatweel at the start of a word.", x={"b": "بيت", "r": TATWEEL + "بيت"})
C("tatweel", "بيت" + TATWEEL, "Tatweel at the end of a word.", x={"b": "بيت"})
C("tatweel", TATWEEL * 3, "A string of tatweels only: the folding policies return an empty string.", level="should",
  x={"b": "", "a": "", "r": TATWEEL * 3})
C("tatweel", "ا" + TATWEEL + HAMZA_A, "A tatweel between alef and a combining hamza blocks NFC composition; after the tatweel is removed, the alef rule removes the hamza on the bare alef.",
  x={"c": "ا" + TATWEEL + HAMZA_A, "r": "ا" + TATWEEL + HAMZA_A, "b": "ا"})
C("tatweel", "ش" + TATWEEL + SHADDA + FATHA + "د", "Shadda and fatha on a tatweel, written in non-canonical order (NFC puts fatha, class 30, before shadda, class 33).",
  x={"c": "ش" + TATWEEL + FATHA + SHADDA + "د", "b": "شد"})
C("tatweel", "ى" + TATWEEL + HAMZA_A, "Alef maqsura, tatweel and combining hamza: after tatweel removal and the alef maqsura to yeh rule, the final NFC pass composes yeh plus hamza into U+0626.",
  x={"b": "ئ", "r": "ى" + TATWEEL + HAMZA_A})
C("tatweel", "سعـر ١٠ ريـالات", "Tatweel in a phrase with Arabic-Indic digits.", x={"b": "سعر 10 ريالات", "a": "سعر 10 ريالات"})
C("tatweel", "گـل", "Tatweel after a Persian letter: the letter is kept.", lang="fa", keep="گ", x={"b": "گل"})
C("tatweel", "لـا", "Tatweel between lam and alef: removal gives the plain lam-alef sequence, not a ligature code point.", x={"b": "لا"})
C("tatweel", "قـــــــال", "A long run of tatweels used for justification.", x={"b": "قال"})

# ------------------------------------------------------------------------------------------------ hamza (23)
C("hamza", "ماء", "Standalone hamza U+0621 is a letter and is kept by every policy.", x={"b": "ماء", "a": "ماء"})
C("hamza", "شيء", "Final standalone hamza after yeh.", x={"b": "شيء"})
C("hamza", "أحمد", "Precomposed alef with hamza above U+0623: folded to bare alef by bayanat-norm-v1 (lossy).", x={"b": "احمد", "c": "أحمد"})
C("hamza", "ا" + HAMZA_A + "حمد", "Decomposed alef + combining hamza above: NFC composes U+0623.", x={"c": "أحمد", "r": "أحمد", "b": "احمد"})
C("hamza", "إسلام", "Precomposed alef with hamza below U+0625.", x={"b": "اسلام"})
C("hamza", "ا" + HAMZA_B + "سلام", "Decomposed alef + combining hamza below: NFC composes U+0625.", x={"c": "إسلام", "b": "اسلام"})
C("hamza", "مؤمن", "Waw with hamza above U+0624 is kept: bayanat-norm-v1 does not fold hamza carriers.", x={"b": "مؤمن", "a": "مؤمن"})
C("hamza", "مو" + HAMZA_A + "من", "Decomposed waw + combining hamza: NFC composes U+0624.", x={"c": "مؤمن", "b": "مؤمن"})
C("hamza", "سائل", "Yeh with hamza above U+0626 is kept.", x={"b": "سائل"})
C("hamza", "سا" + "ي" + HAMZA_A + "ل", "Decomposed yeh + combining hamza: NFC composes U+0626.", x={"c": "سائل", "b": "سائل"})
C("hamza", "ى" + HAMZA_A, "Alef maqsura + combining hamza has no precomposed form, so NFC keeps it; bayanat-norm-v1 maps alef maqsura to yeh and the final NFC pass then composes U+0626.",
  x={"c": "ى" + HAMZA_A, "r": "ى" + HAMZA_A, "b": "ئ"})
C("hamza", "خانه" + HAMZA_A + " من", "Persian heh + combining hamza (ezafe): no precomposed form; the combining hamza is not a haraka and stays in every policy.", lang="fa",
  x={"c": "خانه" + HAMZA_A + " من", "b": "خانه" + HAMZA_A + " من"})
C("hamza", "ە" + HAMZA_A, "Ae U+06D5 + combining hamza: NFC composes U+06C0.", lang="ckb", x={"c": "ۀ", "b": "ۀ"})
C("hamza", "ہ" + HAMZA_A, "Heh goal U+06C1 + combining hamza: NFC composes U+06C2.", lang="ur", x={"c": "ۂ"})
C("hamza", "ے" + HAMZA_A, "Yeh barree U+06D2 + combining hamza: NFC composes U+06D3.", lang="ur", x={"c": "ۓ"})
C("hamza", "ا" + KASRA + HAMZA_B, "Alef, kasra, then hamza below: the hamza (class 220) is not blocked by the kasra (class 32), so NFC composes U+0625 and keeps the kasra.",
  x={"c": "إ" + KASRA, "b": "ا"})
C("hamza", "ا" + FATHA + HAMZA_A, "Alef, fatha, then hamza above: NFC composes U+0623 across the fatha.", x={"c": "أ" + FATHA, "b": "ا"})
C("hamza", "سُؤَال", "Hamza on waw with harakat: harakat are removed, the carrier is kept.", x={"b": "سؤال"})
C("hamza", "مسؤول", "Waw with hamza in the middle of a word.", x={"b": "مسؤول"})
C("hamza", "أ" + HAMZA_A, "Alef with hamza followed by a second combining hamza: bayanat-norm-v1 folds the alef and removes every hamza or madda mark that follows the bare alef.",
  level="should", x={"c": "أ" + HAMZA_A, "b": "ا"})
C("hamza", "ئ" + HAMZA_A, "Yeh with hamza followed by a second combining hamza: the hamza carrier rule is 'keep', so the extra mark stays.", level="should",
  x={"b": "ئ" + HAMZA_A})
C("hamza", "ٵ", "High hamza alef U+0675 has a compatibility decomposition (alef + high hamza U+0674): NFKC splits it; bayanat-norm-v1 maps only presentation forms and keeps it.",
  lang="kk", x={"k": "اٴ", "b": "ٵ"})
C("hamza", "قرأ", "Final alef with hamza above in a verb.", x={"b": "قرا"})

# ------------------------------------------------------------------------------------------------ alef (18)
C("alef", "آمن", "Alef with madda U+0622 at the start of a word: folded to bare alef (lossy).", x={"b": "امن"})
C("alef", "إلى", "Alef with hamza below and final alef maqsura: both are folded.", x={"b": "الي", "a": "الي"})
C("alef", "قرآن", "Alef with madda inside a word.", x={"b": "قران"})
C("alef", "قرا" + MADDA + "ن", "Decomposed alef + combining madda: NFC composes U+0622.", x={"c": "قرآن", "b": "قران"})
C("alef", "بِسْمِ ٱللَّهِ", "Alef wasla U+0671 is folded to bare alef; harakat are removed.", x={"b": "بسم الله"})
C("alef", "شكراً", "Fathatan written after the final alef.", x={"b": "شكرا"})
C("alef", "شكرًا", "Fathatan written on the letter before the final alef.", x={"b": "شكرا"})
C("alef", "ٲ", "Alef with wavy hamza above U+0672 is not one of the four folded alef letters and is kept.", lang="und", x={"b": "ٲ"})
C("alef", "ٳ", "Alef with wavy hamza below U+0673 is kept.", lang="und", x={"b": "ٳ"})
C("alef", "ݳݴ", "Alef letters U+0773 and U+0774 (Arabic Supplement) are kept.", lang="und", x={"b": "ݳݴ"})
C("alef", "ٱلْكِتَٰبُ", "Uthmani spelling with superscript alef: removing the marks leaves the consonantal skeleton (a documented limitation, not a conversion to modern spelling).",
  level="should", x={"b": "الكتب"})
C("alef", "مآب", "Alef with madda in the middle of a word.", x={"b": "ماب"})
C("alef", "أُمّ", "Alef with hamza and damma, word-final shadda.", x={"b": "ام"})
C("alef", "ا" + FATHA + HAMZA_B, "Alef, fatha, combining hamza below: NFC composes U+0625 and keeps the fatha.", level="should", x={"c": "إ" + FATHA, "b": "ا"})
C("alef", "\U0001EE00", "Arabic mathematical alef U+1EE00: NFKC maps it to U+0627; bayanat-norm-v1 maps only presentation forms and keeps it.",
  lang="und", x={"k": "ا", "b": "\U0001EE00"})
C("alef", "آ" + MADDA, "Alef with madda followed by a second combining madda: the fold removes the extra madda after the bare alef.", level="should", x={"b": "ا"})
C("alef", "إيمان", "Alef with hamza below at the start of a word.", x={"b": "ايمان"})
C("alef", "ٱ", "Alef wasla alone.", x={"b": "ا", "c": "ٱ"})

# ------------------------------------------------------------------------------------------------ yeh (18)
C("yeh", "على", "Final alef maqsura U+0649 is mapped to yeh U+064A by bayanat-norm-v1 (lossy: it merges على and علي).", x={"b": "علي", "r": "على"})
C("yeh", "علي", "Final yeh is unchanged.", x={"b": "علي"})
C("yeh", "مصطفى", "Alef maqsura at the end of a name.", x={"b": "مصطفي"})
C("yeh", "یک", "Farsi yeh U+06CC in Persian text is kept.", lang="fa", keep="ی", x={"b": "یک"})
C("yeh", "علی", "Farsi yeh in Arabic text: the policies do not depend on the language tag and keep U+06CC.", level="should", x={"b": "علی"})
C("yeh", "کتاب", "Keheh U+06A9 is kept (Persian and Urdu letters are not mapped).", lang="fa", keep="ک", x={"b": "کتاب"})
C("yeh", "كتاب", "Arabic kaf U+0643 is unchanged.", x={"b": "كتاب"})
C("yeh", "یہ کتاب ہے", "Urdu sentence with Farsi yeh, keheh, heh goal and yeh barree: every letter is kept.", lang="ur", keep="یکہے", x={"b": "یہ کتاب ہے"})
C("yeh", "ی" + HAMZA_A, "Farsi yeh + combining hamza: U+0626 decomposes to Arabic yeh + hamza, so NFC does not compose this pair.", lang="fa",
  x={"c": "ی" + HAMZA_A, "b": "ی" + HAMZA_A})
C("yeh", "عَلَىٰ", "Alef maqsura with superscript alef: the superscript alef is removed and alef maqsura becomes yeh.", x={"b": "علي"})
C("yeh", "مستشفى", "Alef maqsura at the end of a common noun.", x={"b": "مستشفي"})
C("yeh", "ايران", "Arabic yeh in a Persian word.", lang="fa", x={"b": "ايران"})
C("yeh", "ایران", "Farsi yeh in the same Persian word: the two spellings stay different under every policy.", lang="fa", x={"b": "ایران"})
C("yeh", "ۍ", "Yeh with tail U+06CD is kept.", lang="ps", x={"b": "ۍ"})
C("yeh", "ې", "Letter e U+06D0 is kept.", lang="ug", x={"b": "ې"})
C("yeh", "هدًى", "Alef maqsura with fathatan on the preceding letter.", x={"b": "هدي"})
C("yeh", "كتاب", "Arabic kaf in Persian-tagged text is kept as written.", lang="fa", x={"b": "كتاب"})
C("yeh", "متى؟", "Alef maqsura before an Arabic question mark: asr-eval-v1 also removes the question mark.", x={"b": "متي؟", "a": "متي"})

# ------------------------------------------------------------------------------------------------ taa_marbuta (10)
C("taa_marbuta", "مدرسة", "Taa marbuta is kept by bayanat-norm-v1 and folded to heh by asr-eval-v1 (lossy).", x={"b": "مدرسة", "a": "مدرسه"})
C("taa_marbuta", "مدرسه", "The heh spelling is unchanged by every policy.", x={"b": "مدرسه", "a": "مدرسه"})
C("taa_marbuta", "مَدْرَسَةٌ", "Taa marbuta with dammatan.", x={"b": "مدرسة", "a": "مدرسه"})
C("taa_marbuta", "رحمةً", "Taa marbuta with fathatan.", x={"b": "رحمة"})
C("taa_marbuta", "مدرسة البنات", "Taa marbuta inside a construct phrase.", x={"a": "مدرسه البنات"})
C("taa_marbuta", "ﺓ", "Isolated presentation form of taa marbuta: mapped to U+0629 by the folding policies, then to heh by asr-eval-v1.", x={"b": "ة", "a": "ه", "k": "ة"})
C("taa_marbuta", "ۃ", "Teh marbuta goal U+06C3 (Urdu) is a different letter and is kept.", lang="ur", x={"b": "ۃ", "a": "ۃ"})
C("taa_marbuta", "جميلـة", "Tatweel before a final taa marbuta.", x={"b": "جميلة", "a": "جميله"})
C("taa_marbuta", "رسالة.", "Taa marbuta before a full stop.", x={"b": "رسالة.", "a": "رساله"})
C("taa_marbuta", "خانۀ", "Heh with yeh above U+06C0 (Persian) is kept: Persian letters are not mapped.", lang="fa", x={"b": "خانۀ"})

# ------------------------------------------------------------------------------------------------ diacritic_order (22)
C("diacritic_order", "م" + SHADDA + FATHA, "Shadda (class 33) before fatha (class 30): NFC reorders to fatha, shadda.", x={"c": "م" + FATHA + SHADDA, "r": "م" + FATHA + SHADDA, "b": "م"})
C("diacritic_order", "م" + FATHA + SHADDA, "Fatha before shadda is already in canonical order.", x={"c": "م" + FATHA + SHADDA})
C("diacritic_order", "م" + SHADDA + KASRA, "Shadda before kasra (class 32): reordered.", x={"c": "م" + KASRA + SHADDA})
C("diacritic_order", "م" + SHADDA + DAMMA, "Shadda before damma (class 31): reordered.", x={"c": "م" + DAMMA + SHADDA})
C("diacritic_order", "م" + SHADDA + FATHATAN, "Shadda before fathatan (class 27): reordered.", x={"c": "م" + FATHATAN + SHADDA})
C("diacritic_order", "م" + SHADDA + DAMMATAN, "Shadda before dammatan (class 28): reordered.", x={"c": "م" + DAMMATAN + SHADDA})
C("diacritic_order", "م" + SUKUN + SHADDA, "Sukun (class 34) before shadda (class 33): reordered.", level="should", x={"c": "م" + SHADDA + SUKUN})
C("diacritic_order", "ه" + SUPALEF + SHADDA, "Superscript alef (class 35) before shadda: reordered.", x={"c": "ه" + SHADDA + SUPALEF})
C("diacritic_order", "و" + MADDA + SHADDA, "Madda (class 230) before shadda: reordered.", level="should", x={"c": "و" + SHADDA + MADDA})
C("diacritic_order", "ب" + HAMZA_B + KASRA, "Hamza below (class 220) before kasra: reordered; beh has no composition with hamza below.", x={"c": "ب" + KASRA + HAMZA_B})
C("diacritic_order", "مح" + DAMMA + "م" + SHADDA + FATHA + "د", "A name with shadda written before fatha.", x={"c": "مح" + DAMMA + "م" + FATHA + SHADDA + "د", "b": "محمد"})
C("diacritic_order", "مح" + DAMMA + "م" + FATHA + SHADDA + "د", "The same name in canonical order: its NFC form equals that of the previous case.", x={"b": "محمد"})
C("diacritic_order", "ر" + SHADDA + SUPALEF + FATHA, "Three marks out of order: NFC sorts them to fatha (30), shadda (33), superscript alef (35).",
  x={"c": "ر" + FATHA + SHADDA + SUPALEF, "b": "ر"})
C("diacritic_order", "ب" + DAMMATAN + SHADDA, "Dammatan before shadda is already canonical.", x={"c": "ب" + DAMMATAN + SHADDA})
C("diacritic_order", "م" + DAMMATAN + SHADDA + "م" + SHADDA + DAMMATAN, "Two letters: one canonical, one not.", x={"c": "م" + DAMMATAN + SHADDA + "م" + DAMMATAN + SHADDA})
C("diacritic_order", "ب" + "ٖ" + FATHA, "Subscript alef U+0656 (class 220) before fatha: reordered; bayanat-norm-v1 removes both.", level="should", x={"c": "ب" + FATHA + "ٖ", "b": "ب"})
C("diacritic_order", "ب" + "ٗ" + SHADDA, "Inverted damma U+0657 (class 230) before shadda: reordered.", level="should", x={"c": "ب" + SHADDA + "ٗ"})
C("diacritic_order", "و" + DAMMA + HAMZA_A, "Waw, damma, hamza above: NFC composes U+0624 across the damma.", x={"c": "ؤ" + DAMMA, "b": "ؤ"})
C("diacritic_order", "ي" + SHADDA + HAMZA_A, "Yeh, shadda, hamza above: NFC composes U+0626 across the shadda.", x={"c": "ئ" + SHADDA, "b": "ئ"})
C("diacritic_order", "ا" + HAMZA_A + DAMMA, "Alef, hamza above, damma: NFC composes U+0623 and keeps the damma.", x={"c": "أ" + DAMMA, "b": "ا"})
C("diacritic_order", "إ" + KASRA + "ن" + SHADDA + FATHA + " ا" + "ل" + "ل" + SHADDA + FATHA + "ه" + FATHA,
  "A short phrase with shadda written before fatha twice.", x={"b": "ان الله"})
C("diacritic_order", TATWEEL + SHADDA + FATHA, "Marks on a lone tatweel in non-canonical order: NFC reorders, the folding policies remove everything.", level="should",
  x={"c": TATWEEL + FATHA + SHADDA, "b": ""})

# ------------------------------------------------------------------------------------------------ quranic (18)
C("quranic", "هٰذا", "Superscript alef U+0670 is removed by bayanat-norm-v1, which gives the standard spelling هذا.", x={"b": "هذا", "r": "هٰذا"})
C("quranic", "ذٰلِكَ", "Superscript alef with harakat.", x={"b": "ذلك"})
C("quranic", "مِنۢ بَعْدِ", "Small high meem U+06E2 is a Quranic mark and is removed.", x={"b": "من بعد"})
C("quranic", "يَبۡصُۜطُ", "Small high dotless head of khah U+06E1 and small high seen U+06DC are removed.", x={"b": "يبصط"})
C("quranic", "أُو۟لَٰٓئِكَ", "Small high rounded zero U+06DF, superscript alef and madda in one word.", x={"b": "اولئك"})
C("quranic", "۝١٢", "End of ayah U+06DD (a format character) before an ayah number: removed; the digits become ASCII.", x={"b": "12", "c": "۝١٢"})
C("quranic", "۞ بداية", "Rub el hizb U+06DE is in the Quranic mark set and is removed.", x={"b": " بداية", "a": "بدايه"})
C("quranic", "سجدة ۩", "Place of sajdah U+06E9 is removed.", x={"b": "سجدة ", "a": "سجده"})
C("quranic", "إِنَّهُۥ", "Small waw U+06E5 is removed.", x={"b": "انه"})
C("quranic", "بِهِۦ", "Small yeh U+06E6 is removed.", x={"b": "به"})
C("quranic", "و" + MADDA, "A madda on a letter other than alef stays uncomposed and is removed as a Quranic mark.", x={"c": "و" + MADDA, "b": "و"})
C("quranic", "قالۖ", "Small high ligature sad with lam with alef maksura U+06D6 (a pause mark) is removed.", x={"b": "قال"})
C("quranic", "بۭ", "Small low meem U+06ED is removed.", x={"b": "ب"})
C("quranic", "بؕ", "Small high tah U+0615 is removed.", x={"b": "ب"})
C("quranic", "محمدؐ", "Combining honorific sign U+0610 is kept (and flagged) by bayanat-norm-v1, not removed.", level="should", x={"b": "محمدؐ"})
C("quranic", "بࣰ", "Open fathatan U+08F0 (Arabic Extended-A) is in the Quranic mark set and is removed.", x={"b": "ب"})
C("quranic", "بٚ", "Vowel sign small v above U+065A is a language-specific vowel sign, not a Quranic mark: it is kept.", lang="und", level="should", x={"b": "بٚ"})
C("quranic", "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ", "A fully vocalised phrase with superscript alef.", x={"b": "بسم الله الرحمن الرحيم"})

# ------------------------------------------------------------------------------------------------ digits (24)
C("digits", "١٢٣", "Arabic-Indic digits U+0660..U+0669 become ASCII digits in the folding policies; NFKC keeps them (they have no decomposition).",
  x={"b": "123", "k": "١٢٣", "r": "١٢٣"})
C("digits", "۱۲۳", "Extended Arabic-Indic digits U+06F0..U+06F9 become ASCII digits.", lang="fa", x={"b": "123", "k": "۱۲۳"})
C("digits", "۴۵۶", "Extended digits four to six (Persian and Urdu glyph forms share these code points).", lang="ur", x={"b": "456"})
C("digits", "٣٫١٤", "Arabic decimal separator U+066B is punctuation: kept by bayanat-norm-v1, replaced by a space in asr-eval-v1.", x={"b": "3٫14", "a": "3 14"})
C("digits", "١٬٠٠٠", "Arabic thousands separator U+066C is punctuation: asr-eval-v1 splits the number into two tokens (documented limitation).", level="should", x={"b": "1٬000", "a": "1 000"})
C("digits", "٥٠٪", "Arabic percent sign U+066A is punctuation.", x={"b": "50٪", "a": "50"})
C("digits", "2024 ١٤٤٦", "ASCII and Arabic-Indic numbers side by side.", x={"b": "2024 1446"})
C("digits", "١٢٣abc", "Arabic-Indic digits followed by Latin letters.", x={"b": "123abc"})
C("digits", "-٥", "Hyphen-minus before an Arabic-Indic digit: kept by bayanat-norm-v1; asr-eval-v1 treats it as punctuation.", x={"b": "-5", "a": "5"})
C("digits", "+١", "Plus sign is a math symbol (Sm), not punctuation, and is kept by every policy.", x={"b": "+1", "a": "+1"})
C("digits", "١،٥", "Arabic comma between digits.", x={"b": "1،5", "a": "1 5"})
C("digits", "٣.٥", "ASCII full stop between Arabic-Indic digits.", x={"b": "3.5", "a": "3 5"})
C("digits", "١۲٣", "One number mixing Arabic-Indic and Extended Arabic-Indic digits.", x={"b": "123"})
C("digits", "١٤٤٦/٠٩/٠١", "A date with slashes.", x={"b": "1446/09/01", "a": "1446 09 01"})
C("digits", "الـ٣", "Tatweel between the article and a digit.", x={"b": "ال3"})
C("digits", "١٠٠م²", "Superscript two: NFKC folds it to 2; bayanat-norm-v1 keeps it (only Arabic presentation forms are compatibility-mapped).", x={"k": "١٠٠م2", "b": "100م²"})
C("digits", "１２", "Fullwidth digits: NFKC folds them to ASCII; the folding policies keep them.", lang="und", x={"k": "12", "b": "１２"})
C("digits", "۳٫۵", "Persian decimal number with U+066B.", lang="fa", x={"b": "3٫5"})
C("digits", "؀١٢٣", "Arabic number sign U+0600 (a prepended format character) is kept by every policy.", level="should", x={"b": "؀123", "r": "؀١٢٣"})
C("digits", "٥٠؉", "Arabic-Indic per mille sign U+0609 is punctuation.", x={"b": "50؉", "a": "50"})
C("digits", "١" + NBSP + "٠٠٠", "No-break space as a thousands separator: kept by bayanat-norm-v1, collapsed to a space by asr-eval-v1, folded to a space by NFKC.",
  x={"b": "1" + NBSP + "000", "a": "1 000", "k": "١ ٠٠٠"})
C("digits", "٣ ३", "Arabic-Indic three next to Devanagari three: only the Arabic-script digit is mapped.", lang="und", x={"b": "3 ३"})
C("digits", "\U0001D7D1", "Mathematical bold digit three: NFKC folds it; the folding policies keep it.", lang="und", x={"k": "3", "b": "\U0001D7D1"})
C("digits", "عندي ٣ كتب", "Digit inside a sentence.", x={"b": "عندي 3 كتب"})

# ------------------------------------------------------------------------------------------------ presentation_forms (26)
C("presentation_forms", "ﺍ", "Isolated alef presentation form: NFKC and the folding policies map it to U+0627; NFC and raw-safe-v1 keep it.",
  x={"k": "ا", "b": "ا", "c": "ﺍ", "r": "ﺍ"})
C("presentation_forms", "ﻛﺘﺎﺏ", "A word in initial, medial and final forms.", x={"k": "كتاب", "b": "كتاب", "r": "ﻛﺘﺎﺏ"})
C("presentation_forms", "ﺍﻟﻌﺮﺑﻴﺔ", "A word with a final taa marbuta form.", x={"b": "العربية", "a": "العربيه"})
C("presentation_forms", "ﮊ", "Jeh isolated form (Arabic Presentation Forms-A).", lang="fa", x={"b": "ژ", "k": "ژ"})
C("presentation_forms", "ﭖ", "Peh isolated form maps to U+067E, which is then kept.", lang="fa", x={"b": "پ"})
C("presentation_forms", "ﭪ", "Veh isolated form maps to U+06A4, which is then kept.", x={"b": "ڤ"})
C("presentation_forms", "ﮒ", "Gaf isolated form maps to U+06AF.", lang="fa", x={"b": "گ"})
C("presentation_forms", "ﭺ", "Tcheh isolated form maps to U+0686.", lang="fa", x={"b": "چ"})
C("presentation_forms", "ﯼ", "Farsi yeh isolated form maps to U+06CC, which is then kept (not mapped to Arabic yeh).", lang="fa", x={"b": "ی"})
C("presentation_forms", "ﻰ", "Alef maqsura final form maps to U+0649, which bayanat-norm-v1 then maps to yeh.", x={"k": "ى", "b": "ي"})
C("presentation_forms", "ﷲ", "Allah ligature U+FDF2: NFKC expands it to four letters; the folding policies keep it as one character (honorific ligatures are flagged, not expanded).",
  level="should", x={"k": "الله", "b": "ﷲ", "r": "ﷲ"})
C("presentation_forms", "ﷺ", "Salla ligature U+FDFA: NFKC expands it to a four-word phrase (18 code points); the folding policies keep it.",
  level="should", x={"k": "صلى الله عليه وسلم", "b": "ﷺ", "a": "ﷺ"})
C("presentation_forms", "ﷻ", "Jallajalalouhou ligature U+FDFB: NFKC expands it to two words.", level="should", x={"k": "جل جلاله", "b": "ﷻ"})
C("presentation_forms", "﷽", "Bismillah ligature U+FDFD has no decomposition: every policy keeps it.", x={"k": "﷽", "b": "﷽"})
C("presentation_forms", "﷼", "Rial sign U+FDFC: NFKC expands it to four letters; it lies in the honorific range U+FDF0..U+FDFF, so the folding policies keep it.",
  level="should", lang="fa", x={"k": "ریال", "b": "﷼"})
C("presentation_forms", "ﹰ", "Isolated fathatan form: NFKC gives space + fathatan; bayanat-norm-v1 then removes the haraka and keeps the space; asr-eval-v1 trims it to an empty string.",
  level="should", x={"k": " " + FATHATAN, "b": " ", "a": ""})
C("presentation_forms", "ﹱ", "Tatweel with fathatan form: NFKC gives tatweel + fathatan; the folding policies remove both.", x={"k": TATWEEL + FATHATAN, "b": ""})
C("presentation_forms", "ﹽ", "Shadda medial form (tatweel + shadda).", x={"k": TATWEEL + SHADDA, "b": ""})
C("presentation_forms", "ﱞ", "Shadda with dammatan isolated ligature: NFKC gives space + dammatan + shadda.", level="should", x={"k": " " + DAMMATAN + SHADDA, "b": " "})
C("presentation_forms", "ﰈ", "Two-letter ligature beh with meem.", x={"k": "بم", "b": "بم"})
C("presentation_forms", "﴾ب﴿", "Ornate parentheses U+FD3E and U+FD3F have no decomposition and are punctuation.", x={"k": "﴾ب﴿", "b": "﴾ب﴿", "a": "ب"})
C("presentation_forms", "ﷰ", "Salla used as a Koranic stop sign U+FDF0 is in the honorific range and is kept by the folding policies; NFKC expands it.", level="should", x={"k": "صلے", "b": "ﷰ"})
C("presentation_forms", "ﺀ", "Isolated hamza form.", x={"b": "ء"})
C("presentation_forms", "ﺳﺎﺋﻞ", "A word with the initial form of yeh with hamza above.", x={"b": "سائل"})
C("presentation_forms", "ﺏ" + FATHA, "An isolated beh form followed by a combining fatha.", x={"k": "ب" + FATHA, "b": "ب", "c": "ﺏ" + FATHA})
C("presentation_forms", "ﹶ", "Isolated fatha form: NFKC gives space + fatha.", level="should", x={"k": " " + FATHA, "b": " ", "a": ""})

# ------------------------------------------------------------------------------------------------ lam_alef (14)
C("lam_alef", "ﻻ", "Lam-alef ligature, isolated: mapped to lam + alef.", x={"k": "لا", "b": "لا", "r": "ﻻ"})
C("lam_alef", "ﻼ", "Lam-alef ligature, final.", x={"k": "لا", "b": "لا"})
C("lam_alef", "ﻵ", "Lam-alef with madda, isolated: NFKC gives lam + U+0622; bayanat-norm-v1 then folds the alef.", x={"k": "لآ", "b": "لا"})
C("lam_alef", "ﻶ", "Lam-alef with madda, final.", x={"k": "لآ", "b": "لا"})
C("lam_alef", "ﻷ", "Lam-alef with hamza above, isolated.", x={"k": "لأ", "b": "لا"})
C("lam_alef", "ﻸ", "Lam-alef with hamza above, final.", x={"k": "لأ", "b": "لا"})
C("lam_alef", "ﻹ", "Lam-alef with hamza below, isolated.", x={"k": "لإ", "b": "لا"})
C("lam_alef", "ﻺ", "Lam-alef with hamza below, final.", x={"k": "لإ", "b": "لا"})
C("lam_alef", "لا", "Lam and alef as two letters: every policy keeps them.", x={"k": "لا", "b": "لا", "a": "لا"})
C("lam_alef", "ﻻﻋﺐ", "A word starting with the lam-alef ligature.", x={"b": "لاعب"})
C("lam_alef", "ﺍﻟﺴﻼﻡ", "A word with a final lam-alef ligature in the middle.", x={"b": "السلام"})
C("lam_alef", "ل" + ZWJ + "ا", "ZWJ between lam and alef is not part of an emoji sequence and is removed.", x={"b": "لا", "r": "لا", "c": "ل" + ZWJ + "ا"})
C("lam_alef", "ل" + ZWNJ + "ا", "ZWNJ between lam (dual-joining) and alef (right-joining) prevents a join and is kept.", level="should", x={"b": "ل" + ZWNJ + "ا", "r": "ل" + ZWNJ + "ا"})
C("lam_alef", "ﻻ" + FATHA, "Lam-alef ligature followed by a fatha.", x={"k": "لا" + FATHA, "b": "لا"})

# ------------------------------------------------------------------------------------------------ joiners (18)
C("joiners", "می" + ZWNJ + "خواهم", "Persian ZWNJ between two dual-joining letters prevents a join: kept by every policy.", lang="fa", keep=ZWNJ,
  x={"r": "می" + ZWNJ + "خواهم", "b": "می" + ZWNJ + "خواهم"})
C("joiners", "نامه" + ZWNJ + "ها", "Persian plural with ZWNJ after heh.", lang="fa", keep=ZWNJ, x={"b": "نامه" + ZWNJ + "ها"})
C("joiners", "د" + ZWNJ + "ر", "ZWNJ after a right-joining letter (dal) changes nothing and is removed.", x={"r": "در", "b": "در", "c": "د" + ZWNJ + "ر"})
C("joiners", "کتاب" + ZWNJ + " ", "ZWNJ before a space is removed; bayanat-norm-v1 keeps the space, asr-eval-v1 trims it.", lang="fa", x={"b": "کتاب ", "a": "کتاب"})
C("joiners", "ب" + ZWNJ + "ت", "ZWNJ between two dual-joining Arabic letters: kept (the policies do not depend on the language tag).", level="should", x={"b": "ب" + ZWNJ + "ت"})
C("joiners", "ب" + ZWNJ + ZWNJ + "ت", "Two ZWNJs in a row: each skips the other when it looks for its neighbours, so both are kept.", level="should", x={"b": "ب" + ZWNJ + ZWNJ + "ت"})
C("joiners", "ب" + ZWNJ + TATWEEL + " ", "ZWNJ before a tatweel and a space: the neighbour test skips the tatweel and finds a space, so the ZWNJ is removed even by raw-safe-v1 (documented edge).",
  level="should", x={"r": "ب" + TATWEEL + " ", "b": "ب "})
C("joiners", "ب" + ZWNJ + TATWEEL + "ت", "ZWNJ before a tatweel and a joining letter is kept; bayanat-norm-v1 then removes the tatweel.", level="should",
  x={"r": "ب" + ZWNJ + TATWEEL + "ت", "b": "ب" + ZWNJ + "ت"})
C("joiners", "ب" + ZWJ + "ب", "ZWJ between Arabic letters is not part of an emoji sequence and is removed.", x={"r": "بب", "b": "بب"})
C("joiners", "\U0001F468" + ZWJ + "\U0001F469" + ZWJ + "\U0001F467", "Emoji ZWJ sequence: both ZWJs are kept.", lang="und", keep=ZWJ,
  x={"b": "\U0001F468" + ZWJ + "\U0001F469" + ZWJ + "\U0001F467"})
C("joiners", "\U0001F469\U0001F3FD" + ZWJ + "\U0001F4BB", "Emoji ZWJ sequence with a skin-tone modifier before the ZWJ.", lang="und", keep=ZWJ,
  x={"b": "\U0001F469\U0001F3FD" + ZWJ + "\U0001F4BB"})
C("joiners", "❤️" + ZWJ + "\U0001F525", "Emoji ZWJ sequence with a variation selector before the ZWJ.", lang="und", keep=ZWJ,
  x={"b": "❤️" + ZWJ + "\U0001F525"})
C("joiners", "كتاب" + ZWSP + "جديد", "ZWSP between two words is removed without inserting a space, so the words run together (documented behaviour).",
  level="should", x={"r": "كتابجديد", "b": "كتابجديد", "a": "كتابجديد"})
C("joiners", BOM + "مرحبا", "BOM at the start of the text is removed.", x={"r": "مرحبا", "b": "مرحبا", "c": BOM + "مرحبا", "k": BOM + "مرحبا"})
C("joiners", "مر" + BOM + "حبا", "U+FEFF inside a word (used as a zero-width no-break space) is removed.", x={"r": "مرحبا"})
C("joiners", "क्" + ZWNJ + "ष", "ZWNJ after a virama is kept (Devanagari control case for the virama rule).", lang="hi", level="should", x={"r": "क्" + ZWNJ + "ष"})
C("joiners", "مدر­سة", "Soft hyphen inside a word is removed.", x={"r": "مدرسة", "a": "مدرسه"})
C("joiners", "ب" + FATHA + ZWNJ + "ت", "ZWNJ after a letter with a haraka: the neighbour test skips the mark, so the ZWNJ is kept.", level="should",
  x={"r": "ب" + FATHA + ZWNJ + "ت", "b": "ب" + ZWNJ + "ت"})

# ------------------------------------------------------------------------------------------------ bidi (18)
C("bidi", "مرحبا" + RLM, "Right-to-left mark after Arabic text is removed by the cleaning policies and kept by NFC/NFKC.", x={"r": "مرحبا", "c": "مرحبا" + RLM})
C("bidi", LRM + "abc مرحبا", "Left-to-right mark at the start.", x={"r": "abc مرحبا"})
C("bidi", "١" + ALM + "٢", "Arabic letter mark U+061C between digits.", x={"r": "١٢", "b": "12"})
C("bidi", RLE + "مرحبا" + PDF, "Right-to-left embedding and pop.", x={"r": "مرحبا"})
C("bidi", LRE + "abc" + PDF, "Left-to-right embedding and pop.", lang="en", x={"r": "abc"})
C("bidi", RLO + "abc" + PDF, "Right-to-left override (displays the Latin text reversed): removed.", lang="en", x={"r": "abc"})
C("bidi", LRO + "مرحبا" + PDF, "Left-to-right override on Arabic text: removed.", x={"r": "مرحبا"})
C("bidi", RLI + "مرحبا" + PDI, "Right-to-left isolate and pop isolate.", x={"r": "مرحبا"})
C("bidi", LRI + "abc" + PDI + " مرحبا", "Left-to-right isolate before Arabic text.", x={"r": "abc مرحبا"})
C("bidi", FSI + "مرحبا" + PDI, "First-strong isolate.", x={"r": "مرحبا"})
C("bidi", "admin" + RLO + LRI + " // check" + PDI + LRI, "Bidi controls arranged to reorder source text on screen (a reordering attack pattern): all are removed.", lang="en",
  level="should", x={"r": "admin // check", "a": "admin check"})
C("bidi", "مرحبا" + PDF, "A pop directional formatting without an opening control is removed.", x={"r": "مرحبا"})
C("bidi", LRI + "١٢٣" + PDI, "Isolated Arabic-Indic number.", x={"b": "123"})
C("bidi", "النسخة" + RLM + " 2.0", "RLM after an Arabic word followed by a version number.", x={"r": "النسخة 2.0", "a": "النسخه 2 0"})
C("bidi", "مر" + RLM + "حبا", "RLM inside a word is removed.", x={"r": "مرحبا"})
C("bidi", "٢٠٢٤" + LRM + "/" + LRM + "٠١", "LRMs around a slash in a date.", x={"b": "2024/01"})
C("bidi", "ب" + RLM + FATHA, "RLM between a letter and its haraka: removed, leaving the haraka on the letter.", level="should", x={"r": "ب" + FATHA, "c": "ب" + RLM + FATHA})
C("bidi", "ا" + RLM + HAMZA_A, "RLM between alef and combining hamza blocks NFC composition; once the RLM is removed, NFC composes U+0623.", level="should",
  x={"c": "ا" + RLM + HAMZA_A, "r": "أ", "b": "ا"})

# ------------------------------------------------------------------------------------------------ punctuation (14)
C("punctuation", "نعم، لا", "Arabic comma U+060C: kept by bayanat-norm-v1, replaced by a space and collapsed by asr-eval-v1.", x={"b": "نعم، لا", "a": "نعم لا"})
C("punctuation", "أولا؛ ثانيا", "Arabic semicolon U+061B.", x={"a": "اولا ثانيا"})
C("punctuation", "كيف حالك؟", "Arabic question mark U+061F.", x={"b": "كيف حالك؟", "a": "كيف حالك"})
C("punctuation", "«مرحبا»", "Guillemets.", x={"a": "مرحبا"})
C("punctuation", "یہ کتاب ہے۔", "Arabic full stop U+06D4 (Urdu).", lang="ur", x={"a": "یہ کتاب ہے"})
C("punctuation", "مرحبا!", "ASCII exclamation mark after Arabic text.", x={"a": "مرحبا"})
C("punctuation", "نجمة ٭", "Arabic five pointed star U+066D is punctuation.", x={"a": "نجمه"})
C("punctuation", "﴿بسم﴾", "Ornate parentheses in reading order.", x={"a": "بسم"})
C("punctuation", "كتاب،قلم", "Arabic comma without spaces: asr-eval-v1 replaces it with a space, so the words stay apart.", x={"a": "كتاب قلم"})
C("punctuation", "؍", "Arabic date separator U+060D alone.", x={"b": "؍", "a": ""})
C("punctuation", "ب؞ت", "Arabic triple dot punctuation mark U+061E.", x={"a": "ب ت"})
C("punctuation", "“كتاب”", "Curly double quotation marks.", x={"a": "كتاب"})
C("punctuation", "عربي-إنجليزي", "Hyphen between two words.", x={"a": "عربي انجليزي"})
C("punctuation", "انتهى…", "Horizontal ellipsis: NFKC turns it into three full stops; asr-eval-v1 removes it.", x={"k": "انتهى...", "b": "انتهي…", "a": "انتهي"})

# ------------------------------------------------------------------------------------------------ spaces (12)
C("spaces", "كتاب" + NBSP + "جديد", "No-break space U+00A0: kept by bayanat-norm-v1, becomes a space in asr-eval-v1 and NFKC.", x={"b": "كتاب" + NBSP + "جديد", "a": "كتاب جديد", "k": "كتاب جديد"})
C("spaces", "كتاب" + NNBSP + "جديد", "Narrow no-break space U+202F.", x={"a": "كتاب جديد", "k": "كتاب جديد"})
C("spaces", "كتاب" + THIN + "جديد", "Thin space U+2009.", x={"a": "كتاب جديد", "k": "كتاب جديد"})
C("spaces", "كتاب جديد", "Em space U+2003.", x={"a": "كتاب جديد"})
C("spaces", "كتاب　جديد", "Ideographic space U+3000.", x={"a": "كتاب جديد"})
C("spaces", "كتاب   جديد", "Three ASCII spaces: collapsed by asr-eval-v1 only.", x={"b": "كتاب   جديد", "a": "كتاب جديد"})
C("spaces", "  مرحبا  ", "Leading and trailing spaces: trimmed by asr-eval-v1 only.", x={"b": "  مرحبا  ", "a": "مرحبا"})
C("spaces", "سطر\tأول\nسطر", "Tab and line feed are whitespace.", x={"a": "سطر اول سطر", "b": "سطر\tاول\nسطر"})
C("spaces", "سطر\u0085سطر", "Next line U+0085 is a whitespace control and is not rejected.", x={"r": "سطر\u0085سطر", "a": "سطر سطر"})
C("spaces", "سطر سطر", "Line separator U+2028.", x={"a": "سطر سطر"})
C("spaces", NBSP, "A no-break space alone.", x={"b": NBSP, "a": "", "k": " "})
C("spaces", "كتاب جديد", "Medium mathematical space U+205F.", x={"a": "كتاب جديد", "k": "كتاب جديد"})

# ------------------------------------------------------------------------------------------------ mixed_script (10)
C("mixed_script", "مرحبا Hello", "Latin letter case is kept by every policy.", x={"b": "مرحبا Hello", "a": "مرحبا Hello"})
C("mixed_script", "7abibi 3arabi", "Arabizi: Latin letters with digits standing for Arabic sounds are unchanged.", lang="ar-Latn", x={"b": "7abibi 3arabi", "a": "7abibi 3arabi"})
C("mixed_script", "شكرا \U0001F64F", "Emoji after Arabic text is kept.", x={"b": "شكرا \U0001F64F"})
C("mixed_script", "ﬁle عربي", "Latin ligature fi: NFKC folds it, the folding policies keep it.", x={"k": "file عربي", "b": "ﬁle عربي"})
C("mixed_script", "ＡＢＣ عربي", "Fullwidth Latin letters: NFKC folds them, the folding policies keep them.", x={"k": "ABC عربي", "b": "ＡＢＣ عربي"})
C("mixed_script", "שלום سلام", "Hebrew and Arabic words side by side.", lang="und", x={"b": "שלום سلام"})
C("mixed_script", "caf" + "é مقهى", "Latin e + combining acute: NFC composes U+00E9 in every policy except identity.", x={"c": "café مقهى", "b": "café مقهي"})
C("mixed_script", "https://example.com/صفحة", "A URL with an Arabic path: asr-eval-v1 replaces the punctuation with spaces.", x={"a": "https example com صفحه"})
C("mixed_script", "#عربي", "A hashtag: number sign is punctuation.", x={"a": "عربي", "b": "#عربي"})
C("mixed_script", "كتاب کتاب", "Arabic and Persian spellings of the same word stay different.", lang="und", x={"b": "كتاب کتاب"})

# ------------------------------------------------------------------------------------------------ dialect_letters (15)
C("dialect_letters", "ڤيديو", "Veh U+06A4 (used for /v/ in many dialects) must survive every policy.", keep="ڤ", x={"b": "ڤيديو", "a": "ڤيديو"})
C("dialect_letters", "ڨال", "Qaf with three dots above U+06A8 (Maghrebi /g/) must survive.", lang="ar-DZ", keep="ڨ", x={"b": "ڨال"})
C("dialect_letters", "ݣال", "Keheh with three dots above U+0763 (Moroccan /g/) must survive.", lang="ary", keep="ݣ", x={"b": "ݣال"})
C("dialect_letters", "ڭلب", "Ng U+06AD must survive.", lang="ary", keep="ڭ", x={"b": "ڭلب"})
C("dialect_letters", "پيتزا", "Peh U+067E must survive.", keep="پ", x={"b": "پيتزا"})
C("dialect_letters", "چاي", "Tcheh U+0686 (Gulf and Iraqi /ch/) must survive.", keep="چ", x={"b": "چاي"})
C("dialect_letters", "گال", "Gaf U+06AF (Gulf and Iraqi /g/) must survive.", keep="گ", x={"b": "گال"})
C("dialect_letters", "ڤِيلَّا", "Veh with harakat: the harakat are removed, the letter stays.", keep="ڤ", x={"b": "ڤيلا"})
C("dialect_letters", "ڤـيـلا", "Veh with tatweels.", keep="ڤ", x={"b": "ڤيلا"})
C("dialect_letters", "ﭬﻴﻠﺎ", "Veh initial presentation form in a word: mapped to U+06A4, which then survives.", keep="", x={"b": "ڤيلا"})
C("dialect_letters", "ژاكيت", "Jeh U+0698 must survive.", keep="ژ", x={"b": "ژاكيت"})
C("dialect_letters", "ڢ ڧ", "Maghrebi feh U+06A2 and qaf U+06A7 must survive.", lang="ar-MA", keep="ڢڧ", x={"b": "ڢ ڧ"})
C("dialect_letters", "ۋ", "Ve U+06CB must survive.", lang="ug", keep="ۋ", x={"b": "ۋ"})
C("dialect_letters", "ڵ", "Lam with small v U+06B5 must survive.", lang="ckb", keep="ڵ", x={"b": "ڵ"})
C("dialect_letters", "گُلّ", "Gaf with damma and shadda.", lang="fa", keep="گ", x={"b": "گل"})

# ------------------------------------------------------------------------------------------------ confusables (12)
C("confusables", "٠۰", "Arabic-Indic zero U+0660 and Extended Arabic-Indic zero U+06F0 look alike; both become ASCII 0.", x={"b": "00", "k": "٠۰"})
C("confusables", "٤۴", "Arabic-Indic four and Extended Arabic-Indic four (different glyphs, same value).", x={"b": "44"})
C("confusables", "٥۵", "Arabic-Indic five and Extended Arabic-Indic five.", x={"b": "55"})
C("confusables", "يی", "Arabic yeh and Farsi yeh look alike in final form; the policies keep them apart.", lang="und", x={"b": "يی"})
C("confusables", "كک", "Arabic kaf and keheh: kept apart.", lang="und", x={"b": "كک"})
C("confusables", "هہ", "Heh and heh goal U+06C1: kept apart.", lang="und", x={"b": "هہ"})
C("confusables", "هھ", "Heh and heh doachashmee U+06BE: kept apart.", lang="und", x={"b": "هھ"})
C("confusables", "ا١", "Alef and Arabic-Indic one look alike; only the digit is mapped.", x={"b": "ا1"})
C("confusables", "٥ه", "Arabic-Indic five and heh look alike in some fonts; only the digit is mapped.", x={"b": "5ه"})
C("confusables", "،,", "Arabic comma and ASCII comma: both are punctuation for asr-eval-v1.", x={"b": "،,", "a": ""})
C("confusables", "٪%", "Arabic percent sign and ASCII percent sign are both punctuation (Po).", x={"a": ""})
C("confusables", "ىی", "Alef maqsura and Farsi yeh look alike; only alef maqsura is mapped (to yeh).", lang="und", x={"b": "يی"})

# ------------------------------------------------------------------------------------------------ malformed (14)
C("malformed", FATHA + "كتب", "A combining mark at the start of the text (no base letter): kept by NFC and raw-safe-v1, removed with the other harakat by bayanat-norm-v1.",
  x={"c": FATHA + "كتب", "r": FATHA + "كتب", "b": "كتب"})
C("malformed", HAMZA_A, "A combining hamza alone: it is not a haraka and has no alef to fold, so every policy keeps it.", level="should", x={"b": HAMZA_A, "a": HAMZA_A})
C("malformed", "ب" + FATHA + FATHA, "Doubled fatha: NFC keeps both; bayanat-norm-v1 removes both.", x={"c": "ب" + FATHA + FATHA, "b": "ب"})
C("malformed", "ب" + SHADDA + SHADDA + SHADDA, "Tripled shadda.", x={"b": "ب"})
C("malformed", "ب\ud800ت", "A lone high surrogate (possible in Python strings and JSON): removed by the cleaning policies; NFC/NFKC in Python pass it through.",
  x={"r": "بت", "b": "بت", "c": "ب\ud800ت"})
C("malformed", "ب\udc00", "A lone low surrogate at the end.", x={"r": "ب", "c": "ب\udc00"})
C("malformed", "ب﷐", "Noncharacter U+FDD0 (inside the Arabic Presentation Forms-A block) is removed by the cleaning policies.", x={"r": "ب", "c": "ب﷐"})
C("malformed", "ب￾", "Noncharacter U+FFFE is removed.", x={"r": "ب"})
C("malformed", "ب\u0001ت", "C0 control U+0001 is removed.", x={"r": "بت", "c": "ب\u0001ت"})
C("malformed", "ب\u0090ت", "C1 control U+0090 is removed.", x={"r": "بت"})
C("malformed", "ب�ت", "The replacement character U+FFFD is a valid character and is kept.", x={"r": "ب�ت", "b": "ب�ت"})
B("malformed", "d8a7d8", "Truncated UTF-8: the last byte starts a two-byte sequence that never ends. Every policy rejects the input.")
B("malformed", "80d8a7", "A UTF-8 continuation byte with no lead byte.")
B("malformed", "eda080", "UTF-8 encoding of the surrogate U+D800, which is not valid UTF-8.")
