# metaspector/matrices/language_matrix.py
# !/usr/bin/env python3

from typing import List, Tuple, Optional


def get_language_matrix() -> List[Tuple[str, ...]]:
    """Returns the comprehensive language matrices."""
    language_matrix_references = [
        ("aa-ET", "aa", "aar", "Afar", "Qafar af", "Ethiopia"),
        ("ab-GE", "ab", "abk", "Abkhazian", "аҧсуа бызшәа", "Georgia"),
        ("ae-IR", "ae", "ave", "Avestan", "Avesta", "Iran"),
        ("af-ZA", "af", "afr", "Afrikaans", "Afrikaans", "South Africa"),
        ("ak-GH", "ak", "aka", "Akan", "Akan", "Ghana"),
        ("am-ET", "am", "amh", "Amharic", "አማርኛ (Amarəñña)", "Ethiopia"),
        ("an-ES", "an", "arg", "Aragonese", "Aragonés", "Spain"),
        ("ar-SA", "ar", "ara", "Arabic", "العربية", "Saudi Arabia"),
        ("as-IN", "as", "asm", "Assamese", "অসমীয়া (Ôxômiya)", "India"),
        ("av-RU", "av", "ava", "Avaric", "Авар мацӏ (Avar maⱬ)", "Russian Federation"),
        ("ay-BO", "ay", "aym", "Aymara", "Aymar aru", "Bolivia"),
        ("az-AZ", "az", "aze", "Azerbaijani", "Azərbaycan dili", "Azerbaijan"),
        ("ba-RU", "ba", "bak", "Bashkir", "Башҡорт теле", "Russian Federation"),
        ("be-BY", "be", "bel", "Belarusian", "беларуская мова", "Belarus"),
        ("bg-BG", "bg", "bul", "Bulgarian", "български език", "Bulgaria"),
        ("bi-VU", "bi", "bis", "Bislama", "Bislama", "Vanuatu"),
        ("bm-ML", "bm", "bam", "Bambara", "Bamanankan", "Mali"),
        ("bn-BD", "bn", "ben", "Bengali", "বাংলা (Bangla)", "Bangladesh"),
        ("bo-CN", "bo", "bod", "Tibetan", "བོད་ཡིག།", "China"),
        ("br-FR", "br", "bre", "Breton", "Brezhoneg", "France"),
        ("bs-BA", "bs", "bos", "Bosnian", "Bosanski jezik", "Bosnia and Herzegovina"),
        ("ca-ES", "ca", "cat", "Catalan", "Català", "Spain"),
        ("ce-RU", "ce", "che", "Chechen", "Нохчийн мотт", "Russian Federation"),
        ("ch-GU", "ch", "cha", "Chamorro", "Chamorru", "Guam"),
        ("co-FR", "co", "cos", "Corsican", "Corsu", "France"),
        ("cr-CA", "cr", "cre", "Cree", "ᓀᐦᐃᔭᐍᐏᐣ", "Canada"),
        ("cs-CZ", "cs", "ces", "Czech", "Český", "Czechia"),
        ("cu-BG", "cu", "chu", "Church Slavic", "Словѣньскъ", "Bulgaria"),
        ("cv-RU", "cv", "chv", "Chuvash", "Чӑвашла", "Russian Federation"),
        ("cy-GB", "cy", "cym", "Welsh", "Cymraeg", "United Kingdom"),
        ("da-DK", "da", "dan", "Danish", "Dansk", "Denmark"),
        ("de-DE", "de", "deu", "German", "Deutsch (Deutschland)", "Germany"),  # Default
        ("de-AT", "de", "deu", "German (Austria)", "Deutsch (Österreich)", "Austria"),
        (
            "de-CH",
            "de",
            "deu",
            "German (Switzerland)",
            "Deutsch (Schweiz)",
            "Switzerland",
        ),
        (
            "de-LI",
            "de",
            "deu",
            "German (Liechtenstein)",
            "Deutsch (Liechtenstein)",
            "Liechtenstein",
        ),
        (
            "en-US",
            "en",
            "eng",
            "English",
            "English (United States)",
            "United States of America",
        ),  # Default
        (
            "en-GB",
            "en",
            "eng",
            "English (United Kingdom)",
            "English (United Kingdom)",
            "United Kingdom",
        ),
        (
            "en-AU",
            "en",
            "eng",
            "English (Australia)",
            "English (Australia)",
            "Australia",
        ),
        ("en-CA", "en", "eng", "English (Canada)", "English (Canada)", "Canada"),
        ("dv-MV", "dv", "div", "Divehi", "ދިވެހި (Divehi)", "Maldives"),
        ("dz-BT", "dz", "dzo", "Dzongkha", "རྫོང་ཁ་ (Dzongkha)", "Bhutan"),
        ("ee-GH", "ee", "ewe", "Ewe", "Ɛʋɛgbɛ", "Ghana"),
        ("el-GR", "el", "ell", "Greek", "Ελληνικά", "Greece"),
        ("eo-001", "eo", "epo", "Esperanto", "Esperanto", "International"),
        ("es-ES", "es", "spa", "Spanish", "Español (España)", "Spain"),  # Default
        (
            "es-419",
            "es",
            "spa",
            "Spanish (Latin America)",
            "Español (Latinoamérica)",
            "Latin America",
        ),
        ("es-MX", "es", "spa", "Spanish (Mexico)", "Español (México)", "Mexico"),
        (
            "es-US",
            "es",
            "spa",
            "Spanish (United States)",
            "Español (Estados Unidos)",
            "United States of America",
        ),
        ("et-EE", "et", "est", "Estonian", "Eesti keel", "Estonia"),
        ("eu-ES", "eu", "eus", "Basque", "Euskara", "Spain"),
        ("fa-IR", "fa", "fas", "Persian", "فارسی", "Iran"),
        ("ff-SN", "ff", "ful", "Fula", "Fulfulde", "Senegal"),
        ("fi-FI", "fi", "fin", "Finnish", "Suomi", "Finland"),
        ("fil-PH", "fil", "phi", "Filipino", "Filipino", "Philippines"),
        ("fj-FJ", "fj", "fij", "Fijian", "Na Vosa Vakaviti", "Fiji"),
        ("fo-FO", "fo", "fao", "Faroese", "Føroyskt", "Faroe Islands"),
        ("fr-FR", "fr", "fra", "French", "Français (France)", "France"),  # Default
        ("fr-CA", "fr", "fra", "French (Canada)", "Français (Canada)", "Canada"),
        ("fy-NL", "fy", "fry", "Western Frisian", "Frysk", "Netherlands"),
        ("ga-IE", "ga", "gle", "Irish", "Gaeilge", "Ireland"),
        ("gd-GB", "gd", "gla", "Scottish Gaelic", "Gàidhlig", "United Kingdom"),
        ("gl-ES", "gl", "glg", "Galician", "Galego", "Spain"),
        ("gn-PY", "gn", "grn", "Guaraní", "Avañe'ẽ", "Paraguay"),
        ("gu-IN", "gu", "guj", "Gujarati", "ગુજરાત (Gujarātī)", "India"),
        ("gv-IM", "gv", "glv", "Manx", "Gaelg", "Isle of Man"),
        ("ha-NG", "ha", "hau", "Hausa", "هَوُس (Hausa)َ", "Nigeria"),
        ("he-IL", "he", "heb", "Hebrew", "עברית", "Israel"),
        ("hi-IN", "hi", "hin", "Hindi", "मानक हिन्दी", "India"),
        ("ho-PG", "ho", "hmo", "Hiri Motu", "Hiri Motu", "Papua New Guinea"),
        ("hr-HR", "hr", "hrv", "Croatian", "Hrvatski", "Croatia"),
        ("ht-HT", "ht", "hat", "Haitian Creole", "Kreyòl Ayisyen", "Haiti"),
        ("hu-HU", "hu", "hun", "Hungarian", "Magyar", "Hungary"),
        ("hy-AM", "hy", "hye", "Armenian", "հայերեն (Hayeren)", "Armenia"),
        ("hz-NA", "hz", "her", "Herero", "Otjiherero", "Namibia"),
        ("ia-001", "ia", "ina", "Interlingua", "Interlingua", "International"),
        ("id-ID", "id", "ind", "Indonesian", "Bahasa (Indonesia)", "Indonesia"),
        ("ie-001", "ie", "ile", "Interlingue", "Interlingue", "International"),
        ("ig-NG", "ig", "ibo", "Igbo", "Igbo", "Nigeria"),
        ("ii-CN", "ii", "iii", "Nuosu", "Nuosu, ꆈꌠꉙ", "China"),
        ("ik-US", "ik", "ipk", "Inupiaq", "Iñupiaq", "United States of America"),
        ("io-001", "io", "ido", "Ido", "Ido", "International"),
        ("is-IS", "is", "isl", "Icelandic", "Íslenska", "Iceland"),
        ("it-IT", "it", "ita", "Italian", "Italiano", "Italy"),
        ("iu-CA", "iu", "iku", "Inuktitut", "ᐃᓄᒃᑎᑐᑦ (Inuktitut)", "Canada"),
        ("ja-JP", "ja", "jpn", "Japanese", "日本語", "Japan"),
        ("jv-ID", "jv", "jav", "Javanese", "Jawa", "Indonesia"),
        ("ka-GE", "ka", "kat", "Georgian", "ქართული", "Georgia"),
        ("kg-CD", "kg", "kon", "Kongo", "KiKongo", "Congo, DR"),
        ("ki-KE", "ki", "kik", "Kikuyu", "Gĩgĩkũyũ", "Kenya"),
        ("kj-NA", "kj", "kua", "Kwanyama", "Oshikwanyama", "Namibia"),
        ("kk-KZ", "kk", "kaz", "Kazakh", "қазақ тілі", "Kazakhstan"),
        ("kl-GL", "kl", "kal", "Kalaallisut", "Kalaallisut", "Greenland"),
        ("km-KH", "km", "khm", "Khmer", "ខ្មែរ (Khmer)", "Cambodia"),
        ("kn-IN", "kn", "kan", "Kannada", "ಕನ್ನಡ", "India"),
        ("ko-KR", "ko", "kor", "Korean", "한국말", "Korea"),
        ("kr-NG", "kr", "kau", "Kanuri", "Kanuri", "Nigeria"),
        ("ks-IN", "ks", "kas", "Kashmiri", "کٲشُر (Koshur)", "India"),
        ("ku-TR", "ku", "kur", "Kurdish", "Kurdî", "Turkiye"),
        ("kv-RU", "kv", "kom", "Komi", "коми кыв", "Russian Federation"),
        ("kw-GB", "kw", "cor", "Cornish", "Kernewek", "United Kingdom"),
        ("ky-KG", "ky", "kir", "Kyrgyz", "кыргыз тили", "Kyrgyzstan"),
        ("la-VA", "la", "lat", "Latin", "Latina", "Holy See"),
        ("lb-LU", "lb", "ltz", "Luxembourgish", "Lëtzebuergesch", "Luxembourg"),
        ("lg-UG", "lg", "lug", "Ganda", "Luganda", "Uganda"),
        ("li-NL", "li", "lim", "Limburgan", "Lèmburgs", "Netherlands"),
        ("ln-CD", "ln", "lin", "Lingala", "Lingala", "Congo, DR"),
        ("lo-LA", "lo", "lao", "Lao", "ພາສາລາວ", "Lao People's Democratic Republic"),
        ("lt-LT", "lt", "lit", "Lithuanian", "Lietuviškai", "Lithuania"),
        ("lu-CD", "lu", "lub", "Luba-Katanga", "Kiluba", "Congo, DR"),
        ("lv-LV", "lv", "lav", "Latvian", "Latviešu", "Latvia"),
        ("mg-MG", "mg", "mlg", "Malagasy", "Fiteny", "Madagascar"),
        ("mh-MH", "mh", "mah", "Marshallese", "Kajin", "Marshall Islands"),
        ("mi-NZ", "mi", "mri", "Maori", "te reo Māori", "New Zealand"),
        ("mk-MK", "mk", "mkd", "Macedonian", "македонски", "North Macedonia"),
        ("ml-IN", "ml", "mal", "Malayalam", "മലയാളം", "India"),
        ("mn-MN", "mn", "mon", "Mongolian", "Монгол", "Mongolia"),
        ("mo-MD", "mo", "mol", "Moldavian", "молдовеняскэ", "Moldova"),
        ("mr-IN", "mr", "mar", "Marathi", "मराठी", "India"),
        ("ms-MY", "ms", "msa", "Malay", "Bahasa Melayu", "Malaysia"),
        ("mt-MT", "mt", "mlt", "Maltese", "Malti", "Malta"),
        ("my-MM", "my", "mya", "Burmese", "မြန်မာ", "Myanmar"),
        ("na-NR", "na", "nau", "Nauru", "Naoero", "Nauru"),
        ("nb-NO", "nb", "nob", "Norwegian Bokmål", "Norsk bokmål", "Norway"),
        ("nd-ZW", "nd", "nde", "North Ndebele", "isiNdebele", "Zimbabwe"),
        ("ne-NP", "ne", "nep", "Nepali", "नेपाली", "Nepal"),
        ("ng-NA", "ng", "ndo", "Ndonga", "Oshindonga", "Namibia"),
        ("nl-NL", "nl", "nld", "Dutch", "Nederlands", "Netherlands"),
        ("nn-NO", "nn", "nno", "Norwegian Nynorsk", "Norsk nynorsk", "Norway"),
        ("no-NO", "no", "nor", "Norwegian", "Norsk", "Norway"),
        ("nr-ZA", "nr", "nbl", "South Ndebele", "IsiNdebele", "South Africa"),
        ("nv-US", "nv", "nav", "Navajo", "Diné Bizaad", "United States of America"),
        ("ny-MW", "ny", "nya", "Chichewa", "Chicheŵa", "Malawi"),
        ("oc-FR", "oc", "oci", "Occitan", "Occitan", "France"),
        ("oj-CA", "oj", "oji", "Ojibwe", "ᐊᓂᔑᓈᐯᒧᐎᓐ", "Canada"),
        ("om-ET", "om", "orm", "Oromo", "Afaan Oromoo", "Ethiopia"),
        ("or-IN", "or", "ori", "Oriya", "ଓଡ଼ିଆ", "India"),
        ("os-RU", "os", "oss", "Ossetian", "ирон æвзаг", "Russian Federation"),
        ("pa-IN", "pa", "pan", "Panjabi", "ਪੰਜਾਬੀ", "India"),
        ("pi-IN", "pi", "pli", "Pali", "पालि", "India"),
        ("pl-PL", "pl", "pol", "Polish", "Polski", "Poland"),
        ("ps-AF", "ps", "pus", "Pashto", "پښ토", "Afghanistan"),
        (
            "pt-PT",
            "pt",
            "por",
            "Portuguese",
            "Português (Portugal)",
            "Portugal",
        ),  # Default
        ("pt-BR", "pt", "por", "Portuguese (Brazil)", "Português (Brasil)", "Brazil"),
        ("qu-PE", "qu", "que", "Quechua", "Runa Simi", "Peru"),
        ("rc-RE", "rc", "rcf", "Réunion Creole", "Kréol rénioné", "Reunion"),
        ("rm-CH", "rm", "roh", "Romansh", "Rumantsch", "Switzerland"),
        ("rn-BI", "rn", "run", "Ikirundi", "Burundi", "Burundi"),
        ("ro-RO", "ro", "ron", "Romanian", "Româneşte", "Romania"),
        ("ru-RU", "ru", "rus", "Russian", "русский", "Russian Federation"),
        ("rw-RW", "rw", "kin", "Kinyarwanda", "Ikinyarwanda", "Rwanda"),
        ("sa-IN", "sa", "san", "Sanskrit", "संस्कृतम्", "India"),
        ("sc-IT", "sc", "srd", "Sardinian", "Sardu", "Italy"),
        ("sd-PK", "sd", "snd", "Sindhi", "سنڌي", "Pakistan"),
        ("se-NO", "se", "sme", "Northern Sami", "Sámegiella", "Norway"),
        ("sg-CF", "sg", "sag", "Sango", "Sango", "Central African Republic"),
        (
            "sh-BA",
            "sh",
            "hbs",
            "Serbo-Croatian",
            "Srpskohrvatski",
            "Bosnia and Herzegovina",
        ),
        ("si-LK", "si", "sin", "Sinhala", "සිංහල", "Sri Lanka"),
        ("sk-SK", "sk", "slk", "Slovak", "Slovenčina", "Slovakia"),
        ("sl-SI", "sl", "slv", "Slovenian", "Slovenščina", "Slovenia"),
        ("sm-WS", "sm", "smo", "Samoan", "Gagana Samoa", "Samoa"),
        ("sn-ZW", "sn", "sna", "Shona", "Chishona", "Zimbabwe"),
        ("so-SO", "so", "som", "Somali", "Af-Soomaali", "Somalia"),
        ("sq-AL", "sq", "sqi", "Albanian", "Shqip", "Albania"),
        ("sr-RS", "sr", "srp", "Serbian", "српски", "Serbia"),
        ("ss-SZ", "ss", "ssw", "Swati", "siSwati", "Eswatini"),
        ("st-LS", "st", "sot", "Southern Sotho", "Sesotho", "Lesotho"),
        ("su-ID", "su", "sun", "Sundanese", "Basa Sunda", "Indonesia"),
        ("sv-SE", "sv", "swe", "Swedish", "Svenska", "Sweden"),
        ("sw-KE", "sw", "swa", "Swahili", "Kiswahili", "Kenya"),
        ("ta-IN", "ta", "tam", "Tamil", "தமிழ்", "India"),
        ("te-IN", "te", "tel", "తెలుగు", "India"),
        ("tg-TJ", "tg", "tgk", "Tajik", "тоҷикӣ (Tojiki)", "Tajikistan"),
        ("th-TH", "th", "tha", "Thai", "ภาษาไทย‎", "Thailand"),
        ("ti-ER", "ti", "tir", "Tigrinya", "ትግርኛ (Tigrinya)", "Eritrea"),
        ("tk-TM", "tk", "tuk", "Turkmen", "Türkmençe", "Turkmenistan"),
        ("tl-PH", "tl", "tgl", "Tagalog", "Tagalog", "Philippines"),
        ("tn-BW", "tn", "tsn", "Tswana", "Setswana", "Botswana"),
        ("to-TO", "to", "ton", "Tongan", "Faka Tonga", "Tonga"),
        ("tr-TR", "tr", "tur", "Turkish", "Türkçe", "Turkiye"),
        ("ts-ZA", "ts", "tso", "Tsonga", "Xitsonga", "South Africa"),
        ("tt-RU", "tt", "tat", "Tatar", "татарча", "Russian Federation"),
        ("tw-GH", "tw", "twi", "Twi", "Twi", "Ghana"),
        ("ty-PF", "ty", "tah", "Tahitian", "Reo Tahiti", "French Polynesia"),
        (
            "zh-CN",
            "zh",
            "zho",
            "Chinese (Simplified)",
            "中文 (中国大陆)",
            "China",
        ),  # Default
        ("zh-TW", "zh", "zho", "Chinese (Traditional)", "中文 (臺灣)", "Taiwan"),
        ("zh-HK", "zh", "zho", "Chinese (Hong Kong)", "中文 (香港)", "Hong Kong"),
        ("ug-CN", "ug", "uig", "Uyghur", "ئۇيغۇرچە (Uyghurche)", "China"),
        ("uk-UA", "uk", "ukr", "Ukrainian", "українська", "Ukraine"),
        ("ur-PK", "ur", "urd", "Urdu", "اردو (Urdū)", "Pakistan"),
        ("uz-UZ", "uz", "uzb", "Uzbek", "O'zbek", "Uzbekistan"),
        ("ve-ZA", "ve", "ven", "Venda", "Tshivenḓa", "South Africa"),
        ("vi-VN", "vi", "vie", "Vietnamese", "Việt", "Viet Nam"),
        ("vo-001", "vo", "vol", "Volapük", "Volapük", "International"),
        ("wa-BE", "wa", "wln", "Walloon", "Walon", "Belgium"),
        ("wo-SN", "wo", "wol", "Wolof", "Wolof", "Senegal"),
        ("xh-ZA", "xh", "xho", "Xhosa", "isiXhosa", "South Africa"),
        ("yi-001", "yi", "yid", "Yiddish", "ייִדיש", "International"),
        ("yo-NG", "yo", "yor", "Yoruba", "Yorùbá", "Nigeria"),
        ("za-CN", "za", "zha", "Zhuang", "Saɯ cueŋƅ", "China"),
        ("zu-ZA", "zu", "zul", "Zulu", "isiZulu", "South Africa"),
    ]
    return language_matrix_references


_matrix = get_language_matrix()

# Map BCP 47 code (e.g., "en-US") to its long name ("English (United States)")
_bcp47_map = {entry[0]: entry[4] for entry in _matrix}

# Map ISO 639-2/B code (e.g., "eng") to its long name ("English")
# We use the designated default for this mapping
_iso639_2_defaults = {
    "deu": "de-DE",
    "eng": "en-US",
    "spa": "es-ES",
    "fra": "fr-FR",
    "por": "pt-PT",
    "zho": "zh-CN",
}
_iso639_2_map = {
    code: _bcp47_map.get(bcp47) for code, bcp47 in _iso639_2_defaults.items()
}

# Map for 2-letter codes to their designated default BCP 47 code
_iso639_1_defaults = {
    "de": "de-DE",
    "en": "en-US",
    "es": "es-ES",
    "fr": "fr-FR",
    "pt": "pt-PT",
    "zh": "zh-CN",
}


def get_long_language_name(code: str) -> Optional[str]:
    """
    Looks up the long, descriptive language name from various codes.
    - BCP 47 (e.g., "en-US")
    - ISO 639-2/B (e.g., "eng")
    - ISO 639-1 (e.g., "en"), respecting designated defaults.
    """
    if not code:
        return None

    # 1. Direct BCP 47 match (most specific)
    if "-" in code and code in _bcp47_map:
        return _bcp47_map[code]

    # 2. ISO 639-2/B (3-letter) match
    if len(code) == 3 and code in _iso639_2_map:
        return _iso639_2_map[code]

    # 3. ISO 639-1 (2-letter) match using defaults
    if len(code) == 2 and code in _iso639_1_defaults:
        default_bcp47 = _iso639_1_defaults[code]
        return _bcp47_map.get(default_bcp47)

    # Fallback for 3-letter codes without a specified default
    if len(code) == 3:
        for entry in _matrix:
            if entry[2] == code:
                return entry[4]

    # Fallback for 2-letter codes without a specified default
    if len(code) == 2:
        for entry in _matrix:
            if entry[1] == code:
                return entry[4]

    return None
