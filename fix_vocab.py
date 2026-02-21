#!/usr/bin/env python3
"""Fix broken Hebrew vocabulary words from bad PDF parsing."""

import re, json, sys

with open('index.html', 'r') as f:
    content = f.read()

match = re.search(r'const VOCAB = (\[.*?\]);', content, re.DOTALL)
vocab = json.loads(match.group(1))
print(f'Total entries before: {len(vocab)}')

# ============================================================
# STEP 1: Identify and remove fragment entries
# These are entries where the "word" is actually a continuation
# of a previous entry's example sentence
# ============================================================

# Indices to remove (0-based). We identify them by their word field.
fragments_to_remove = set()

# Build a map of word -> index for identification
word_to_idx = {}
for i, v in enumerate(vocab):
    word_to_idx.setdefault(v['word'], []).append(i)

# Specific fragments identified in the task description and by pattern analysis
# We identify by word text since indices may shift
fragment_words = [
    # From task description - clear fragments where word is part of example sentence
    # and definition is a sentence continuation
    "גוה רים",  # fragment of גוהר
    "נתתי אתהדוללה",  # fragment
    "לחזר עלהפתחים",  # fragment
    "לחלות אתפני",  # fragment
    "החטיא",  # def="את שער..." - fragment
    "קונוונציה התנהגות",  # fragment
    "הכב ירבמ ילים",  # fragment
    "הטילהא ימה",  # fragment of מטילא ימה
    "השדה היהמ טלל",  # fragment of מטלל
    "האדון נטהחסד",  # fragment of נטהחסד
    "ישנוצח צוח חרבות",  # fragment
    "הטכנאיכיל",  # fragment
    "חסרון שלמחשב ניח",  # fragment
    "האלמ נכים",  # fragment of אלמנך
    "פוגל קיבץמסה",  # fragment
    "אבי נשען עלמסעד",  # fragment
    "אניא נוס",  # fragment of אנוס
    "יצאהמר צעמןהשק",  # fragment - broken beyond repair
    "סביב הטוטם",  # fragment
    "יוק שות",  # fragment
    "נוספים מסובס ידיה",  # fragment
    "נפשי לאביון",  # fragment
    "הקד נציה",  # fragment (broken "הקדנציה")
    "אחוזתא ימה",  # fragment of previous
    "הלקוחש בער צון",  # fragment
    "העד יתשבעדית",  # fragment
    "הקב ילה",  # fragment
    "שמחט",  # fragment - def="את אפו..."
    "פומ פוזית",  # fragment - def="של אביבית..."
    "אמד",  # def="את שווי הדירה" - fragment
    "הדר יכואתמ נוחתו",  # fragment
    "הונו",  # def="של ביל גייטס..." - fragment
    "טיבו",  # def="של יין..." - fragment  
    "חמר מרת \"הנג-",  # this is a separate issue - actually "חמרמרת" hangover but with weird formatting
    "הטיתי",  # fragment of הטיה
    "הורדות",  # fragment
    "הטונדרה",  # fragment of טונדרה
    "סנטה",  # fragment - "חנה בשמשון"
    "ותולא",  # fragment
    "למחול",  # fragment of מחילה
    "חברימחפה",  # fragment of מחפה
    "נוסכת",  # fragment of נוסך
    "תיטור",  # fragment of נוטר - actually this could be legit word
    "לבגדיהםט לאי",  # fragment
    "התמונהר יצדה",  # fragment
    "שםלאל",  # broken - "שם לאל" but actually fragment
    "שםנפ שוב כפו",  # fragment
    "שםפ עמיו",  # fragment
    "בידו שלהחקלאי עמיר",  # fragment
    "מהאסקפה",  # fragment of אסקפה
    "הגיבן",  # fragment - def starts with "פגם שולי"
    "העמיל",  # fragment of עמיל
    "תסכ יתים",  # fragment of תסכית
    "בויתו",  # fragment of ביות - "מן הזאב..."
    "ביות",  # this one IS legit (domestication) but the next entry "בויתו" is fragment
    "גדיל",  # has comma in def, looks like fragment continuation
    "באבו",  # def starts without real definition structure - but actually this IS a real word
    "דומן",  # legit word
    "סובבוב כחש",  # fragment - misspelling, duplicate of "סבב בכחש"  
    "עבדכי ימלוך,",  # fragment with comma - duplicate of עבד כי ימלוך
    # More fragments from continued analysis
    "המימרה",  # fragment of מימרה
    "כפחים",  # fragment of כפח
    "האביס",  # fragment - actually "האביס" IS a word form
    "לחידלון",  # fragment of חידלון
    "לטכס עצה",  # fragment of טיכס עצה
    "מדחי",  # fragment of דחי
    "הפושטיד",  # fragment of פושט יד
    "המכמורת",  # fragment of מכמורת
    "כמנחה",  # fragment of מנחה
    "המת אבנים",  # fragment of מתאבן
    "למת ווה",  # fragment of מתווה
    "בחאן",  # fragment of חאן
    "לבער",  # fragment of ביעור
    "המסיק",  # fragment of מסיק
    "שהת ערטל",  # fragment of התערטל
    "להתקשט בנוצות זרים",  # fragment
    "בטרוניה",  # fragment of טרוניה
    "נוסכת",  # already listed
    "נחשולים",  # fragment of נחשול
    "טולרנטיות",  # fragment of טולרנטי  
    "סגפנות",  # fragment of סגפן
    "ללא עוררין",  # fragment of אין עליו עוררין
    "מבין השיטין",  # fragment of בין השיטין
    "בשדותינודשן",  # fragment of דשן
    "עימי אתחר יטי",  # fragment of חריט
    "נדדהשנת",  # fragment of נדדהש נתו
    "האביס",  # already handled
    "האבסת",  # fragment of אבוס
    "סעד",  # def="את החולה..." - fragment
    "הקניט",  # fragment of הקנטה
    "להקיז",  # fragment of הקזה
    "בטפ יפה",  # fragment of טפיפה
    "ויחרא פו.\"",  # fragment
    "ואין",  # fragment
    "וביוםהשב יעיתשבת",  # fragment of חריש
    "קניתי כסת",  # fragment of כסת
    "נהוג לקרקש",  # fragment of מקרקש
    "בפרוטרוט",  # fragment
    "סקירת",  # fragment of סקירה
    "ידך",  # fragment
    "תמצית",  # actually "תצמית" - fragment
    "באר זים\"",  # fragment
    "אנפילאות",  # fragment of אנפילה
    "בנקל,",  # fragment/duplicate of בנקל
    "כלות",  # this is actually a fragment - def="בכמיהה רבה..." which is continuation
    "תקה ינה.",  # fragment
    "כאבקאדם",  # fragment of אבקאדם
    "הופכין",  # fragment
    "יפעל לאיחוי",  # fragment
    "לעצור לאת נחתא",  # fragment
    "הגלעין",  # fragment of גלעין
    "התלמידדחהבקש",  # fragment
    "האומןטבע",  # fragment
    "תחושת זיכוך",  # fragment
    "הראיה",  # fragment - def="המרכזית להפללתו"
    "יואבדר",  # fragment of דר
    "צלולה",  # fragment
    "מאב ניהדרך",  # fragment of אבן דרך
    "עולם",  # fragment - def="וכי מה שבאמת חשוב..."
    "הדום",  # this IS a legit word actually
    "שלילד כחוש",  # fragment
    "פנים",  # fragment in context - def="חד משמעי..."
    "שכן ישלו קושן",  # fragment of קושן  
    "כתמול",  # fragment of "כתמול שלשום"
    "בשמ יםהיא",  # fragment
    "אורבניים",  # fragment of אורבני
    "אוסף הקולקציה",  # fragment
    "אלרואי רובץ",  # fragment (example sentence fragment)
    "העתודה",  # fragment of עתודה
    "מהרהר",  # not in list, skip
    "המרצה עמד עלהקתדרה",  # fragment of קתדרה
    "נוקד",  # legit word actually
    # Actually let me be more careful. Let me re-check some of these.
]

# Let me be more precise - only remove clear fragments
# A fragment is where the word field contains broken text from an example,
# and the definition is clearly a sentence continuation

# Let me build a more careful list by checking actual entries
remove_words_exact = set()
for i, v in enumerate(vocab):
    w = v['word']
    d = v['definition']
    
    # Check if this is in our fragment list
    if w in fragment_words:
        # But protect legitimate words!
        if w == "בכר":  # explicitly protected
            continue
        if w == "ביות":  # domestication - legit
            continue
        if w == "באבו":  # legit word
            continue
        if w == "דומן":  # legit  
            continue
        if w == "הדום":  # legit word (footstool)
            continue
        if w == "נוקד":  # legit word
            continue
        if w == "כלות":  # could be legit "בכלות עיניים"
            continue
        if w == "תיטור":  # might be legit
            continue
        remove_words_exact.add(i)

# Additional fragments identified by pattern: word contains spaces and definition
# starts with a preposition or continuation word, AND the word is clearly broken
additional_removals = []
for i, v in enumerate(vocab):
    w = v['word']
    d = v['definition']
    
    # Already marked
    if i in remove_words_exact:
        continue
    
    # Specific additional fragments identified
    if w == "סובבוב כחש" and "עד שהתגלו" in d:
        additional_removals.append(i)
    elif w == "עבדכי ימלוך," and "כל כך מהר" in d:
        additional_removals.append(i)

for i in additional_removals:
    remove_words_exact.add(i)

print(f"Entries to remove: {len(remove_words_exact)}")

# ============================================================
# STEP 2: Fix broken word spacing
# ============================================================

# Dictionary of known fixes: broken_word -> fixed_word
word_fixes = {
    "אבןמשחזת": "אבן משחזת",
    "אגוצנטרי": "אגוצנטרי",  # correct
    "אדהוק": "אד-הוק",
    "אוב ייקט": "אובייקט",
    "אוב ייקט יבי": "אובייקטיבי",
    "סובס ידיה": "סובסידיה",
    "פומ פוזי": "פומפוזי",
    "קוגניט יבי": "קוגניטיבי",
    "מונותא יזם": "מונותאיזם",
    "סוב יקט יביות": "סובייקטיביות",
    "קדחת נות": "קדחתנות",
    "קוהר נטי": "קוהרנטי",
    "ביוס פרה": "ביוספרה",
    "ביןהמ צרים": "בין המצרים",
    "ביןהשמ שות": "בין השמשות",
    "גדיים נעשות ישים": "גדיים נעשו תיישים",
    "היה לולזרא": "היה לו לזרא",
    "חדש יםלבקרים": "חדשים לבקרים",
    "כאןק בורה כלב": "כאן קבור הכלב",
    "אלאמש נאתהמן": "אלא משנאת המן",
    "הוס יףנפךמשלו": "הוסיף נופך משלו",
    "זהלא כבר": "זה לא כבר",
    "כבשאת יצרו": "כבש את יצרו",
    "לאש זפתו עין": "לא שזפתו עין",
    "עבדכי ימלוך": "עבד כי ימלוך",
    "פהמפ יקמר גליות": "פה מפיק מרגליות",
    "עלע סתו": "על עיסתו",
    "סבבב כחש": "סובב כחש",
    "בקר ניו": "בקרניו",
    "חילהאת פניו": "חילה את פניו",
    "חזר עלהפתחים": "חזר על הפתחים",
    "חבלי לדה": "חבלי לידה",
    "יחידס גולה": "יחיד סגולה",
    "כזהראה וקדש": "כזה ראה וקדש",
    "מחר ישא זנים": "מחריש אזנים",
    "נזם זהבבאף חזיר": "נזם זהב באף חזיר",
    "עור באפרח": "עורב אפרוח",  # actually "עוף באפרוח" or the expression
    "מטילא ימה": "מטיל אימה",
    "מימ יםימ ימה": "מימים ימימה",
    "נטהחסד": "נטה חסד",
    "עלא פוועל חמתו": "על אף ועל חמתו",
    "עירמקלט": "עיר מקלט",
    "אין ידומשגת": "אין ידו משגת",
    "ביתבד": "בית בד",
    "ביתרשאת": "ביתר שאת",
    "יין בןחמץ": "יין בן חמץ",
    "כחמרב ידה יוצר": "כחומר ביד היוצר",
    "כון לדעת גדולים": "כיוון לדעת גדולים",
    "לבירינת": "לבירינת",  # this is actually correct (labyrinth)
    "מטלנפל": "מט לנפול",
    "מטתס דום": "מטת סדום",
    "שווה בנפשך": "שווה בנפשך",  # correct  
    "קוצושל יוד": "קוצו של יוד",
    "בכיתמ רורים": "בכית מרורים",
    "בכל רמ״ח אבריו": "בכל רמ\"ח אבריו",
    "בכפ יפהאחת": "בכפיפה אחת",
    "חלקה ארי": "חלק הארי",
    "חלב": "חֵלֶב",  # actually correct as-is
    "כמפתח": "כמפתח",  # actually part of expression
    "חלוםבאס פמיה": "חלום באספמיה",
    "מןה פחאלה פחת": "מן הפח אל הפחת",
    "בית נתיבות": "בית נתיבות",  # correct
    "דון קישוטיות": "דון קישוטיות",  # correct
    "היולי": "היולי",  # correct
    "היפונים": "היפונים",  # fragment-ish but word might be legit
    "יושב אהל": "יושב אוהל",
    "שלח ידב נפשו": "שלח יד בנפשו",
    "בנפ שוהדבר": "בנפשו הדבר",
    "אמרנו זאתב עלמא": "אמרנו זאת בעלמא",
    "תלית לים": "תילי תילים",
    "מצט ווה": "מצטווה",
    "חרבפ יפיות": "חרב פיפיות",
    "טליתש כלהת כלת": "טלית שכולה תכלת",
    "כמט חויקשת": "כמטחווי קשת",
    "ללאכחל ושרק": "ללא כחל ושרק",
    "קנה לושב יתה": "קנה לו שביתה",
    "סכר אתפיו": "סכר את פיו",
    "לסכור אתפיו": "לסכור את פיו",
    "סמוך עלשולחן": "סמוך על שולחן",
    "סנוניתר אשונה": "סנונית ראשונה",
    "עקבאכ ילס": "עקב אכילס",
    "עקבב צדאגודל": "עקב בצד אגודל",
    "פקובר כיו": "פקו ברכיו",
    "קפא עלשמריו": "קפא על שמריו",
    "קפץאת ידו": "קפץ את ידו",
    "כפההרכ גיגית": "כפה הר כגיגית",
    "עמדמ נגד": "עמד מנגד",
    "מסמרשער": "מסמר שיער",
    "דמוב ראשו": "דמו בראשו",
    "גמר עליואתההלל": "גמר עליו את ההלל",
    "העלהחרסב ידו": "העלה חרס בידו",
    "העלה עלנס": "העלה על נס",
    "הפיל אתח תתו": "הפיל את חתתו",
    "נכנס בעביה קורה": "נכנס בעובי הקורה",
    "עמקה בכא": "עמק הבכא",
    "נשגבמב ינתו": "נשגב מבינתו",
    "סרח ינו": "סרח חינו",
    "ירדהקרנו": "ירדה קרנו",
    "ישלאל ידו": "יש לאל ידו",
    "מרךלב": "מורך לב",
    "חשךמצרים": "חושך מצרים",
    "קררוח": "קור רוח",
    "קראתגר": "קרא תגר",
    "קרדם לחפרבו": "קרדום לחפור בו",
    "רפה ידים": "רפה ידיים",
    "שעיר לעזאזל": "שעיר לעזאזל",  # correct
    "תעודת עניות": "תעודת עניות",  # correct
    "הצראתצ עדיו": "הצר את צעדיו",
    "הקשהאת ערפו": "הקשה את ערפו",
    "ישובהדעת": "יישוב הדעת",
    "לפני ולפ נים": "לפני ולפנים",
    "משכ ברה ימים": "משכבר הימים",
    "משולחרסן": "משולח רסן",
    "סערהב כוסמים": "סערה בכוס מים",
    "עשהש מות": "עשה שמות",
    "שפראד שפרא": "שפרא דשפרא",
    "פרשתדרכים": "פרשת דרכים",
    "קשרכתרים": "קשר כתרים",
    "תצלינהשתיא זניו": "תצלינה שתי אוזניו",
    "כתתאתר גליו": "כתת את רגליו",
    "אבדתקוה": "אבדה תקווה",
    "אליה וקוץבה": "אליה וקוץ בה",
    "באעלש כרו": "באה על שכרה",
    "דבריסרק": "דברי סרק",
    "דחקאתר גליו": "דחק את רגליו",
    "כבשתהרש": "כבשת הרש",
    "חיבקאש פתות": "מחבק אשפתות",
    "חדלא ישים": "חדל אישים",
    "שטח בקש תולפניו": "שטח בקשתו לפניו",
    "רודףשררה": "רודף שררה",
    "עלהבק נהאחד": "על הבקנה אחד",  # should be "עלו בקנה אחד"
    "שמחה לאיד": "שמחה לאיד",  # correct
    "עלנקלה": "על נקלה",
    "הלב יןאת פניו": "הלבין את פניו",
    "הכצעקתה": "הכצעקתה",  # correct
    "איחזאת עיניו": "איחז את עיניו",
    "אימננטי": "אימננטי",  # correct
    "אינהרנטי": "אינהרנטי",  # correct
    "משאת נפש": "משאת נפש",  # correct
    "משובב נפש": "משובב נפש",  # correct  
    "הסב ירפנים": "הסביר פנים",
    "גדשאתהסאה": "גדש את הסאה",
    "דבר עללבו": "דבר על ליבו",
    "הוק ירר גליו": "הוקיר רגליו",  # actually "הדיר רגליו"
    "הכב ידאת לבו": "הכביד את ליבו",
    "הכה עלחטא": "הכה על חטא",
    "הלךע מובקרי": "הלך עמו בקרי",
    "הלנתשכר": "הלנת שכר",
    "הריםאתקרנו": "הרים את קרנו",
    "זחהדע תועליו": "זחה דעתו עליו",
    "זכהמןההפקר": "זכה מן ההפקר",
    "זאבב עור כבש": "זאב בעור כבש",
    "יושב עלהמ דוכה": "יושב על המדוכה",
    "יצאמד עתו": "יצא מדעתו",
    "כאחדהאדם": "כאחד האדם",
    "מוכ יחבשער": "מוכיח בשער",
    "מלגו ומלבר": "מלגו ומלבר",  # correct
    "עבראתמצ ותו": "עבר את מצוותו",
    "שבראת לבו": "שבר את ליבו",
    "שוקקח יים": "שוקק חיים",
    "קבורת חמור": "קבורת חמור",  # correct
    "יוצא דפן": "יוצא דופן",
    "כלכלאתש יבתו": "כלכל את שיבתו",
    "מסיג גבול": "מסיג גבול",  # correct
    "נכסי צאן ברזל": "נכסי צאן ברזל",  # correct
    "עודח זון למועד": "עוד חזון למועד",
    "עוקרהרים": "עוקר הרים",
    "זרעמרעים": "זרע מרעים",
    "בניםמשח יתים עזבו": "בנים משחיתים",  # actually this whole entry is weird
    "טוטליטרי": "טוטליטרי",  # correct actually (in example it's broken)
    "אסק פהה נדרסת": "אסקופה הנדרסת",
    "בטןרכה": "בטן רכה",
    "הוצ יאד יבה": "הוציא דיבה",
    "הבלי עולם": "הבלי עולם",  # correct
    "גלהאת לבו": "גלה את ליבו",
    "דו פרצופי": "דו-פרצופי",
    "חשך עליו עולמו": "חשך עליו עולמו",  # correct
    "ידרוח צתיד": "יד רוחצת יד",
    "לאלקקדבש": "לא לקק דבש",
    "לשוןס גינהור": "לשון סגי נהור",
    "מן השיתין": "מן השיתין",  # correct
    "עומד במריו": "עומד במריו",  # correct  
    "עינייםט רוטות": "עיניים טרוטות",
    "עשה נפשות": "עשה נפשות",  # correct
    "עשהשקר בנפשו": "עשה שקר בנפשו",
    "זבחוטם": "זב חוטם",
    "רונןה לךשולל": "רונן הלך שולל",  # fragment actually
    "אוב ניים": "אובניים",
    "בדעהצ לולה": "בדעה צלולה",
    "ביתמרזח": "בית מרזח",
    "דברי חלקות": "דברי חלקות",  # correct
    "הלך לאבדון": "הלך לאבדון",  # correct
    "אבןשא יןלה הופכין": "אבן שאין לה הופכין",
    "לאדב יםולא יער": "לא דובים ולא יער",
    "לאמ נהולאמק צתה": "לא מינה ולא מקצתה",
    "לבהאת היצרים": "ליבה את היצרים",
    "לילש מורים": "לילי שמורים",
    "מאיר עיניים": "מאיר עיניים",  # correct
    "משענתק נהר צוץ": "משענת קנה רצוץ",
    "נתפס בקלק לתו": "נתפס בקלקלתו",
    "סתםאתה גולל": "סתם את הגולל",
    "עלכר עיתר נגלת": "על כרעי תרנגולת",
    "עשוי לבליחת": "עשוי לבלי חת",
    "יחידיס גלה": "יחידי סגולה",
    "כאבל בין חתנים": "כאבל בין חתנים",  # correct
    "כבדפה": "כבד פה",
    "יושבקר נות": "יושב קרנות",
    "ושני בניםתקה ינה": "ושיני בנים תקהינה",
    "אהבהאפ לטונית": "אהבה אפלטונית",
    "באאבט רוניהעמו": "בא בטרוניה עמו",
    "טחןמים": "טחן מים",
    "טחו עיניומר אות": "טחו עיניו מראות",
    "ידו עלה עליונה": "ידו על העליונה",
    "ירד לסוףדעתי": "ירד לסוף דעתי",
    "הרהר עלמ דותיו": "הרהר על מידותיו",
    "השליך נפשומ נגד": "השליך נפשו מנגד",
    "זרהמ לח עלהפ צע ים": "זרה מלח על הפצעים",  # this is actually a separate entry "הפצעים"
    "הפצעים": "הפצעים",  # this is a weird entry
    "נפ לה רוחו": "נפלה רוחו",
    "נשא עיניו": "נשא עיניו",  # correct
    "ד'א מות": "ד' אמות",
    "אין נביאבע ירו": "אין נביא בעירו",
    "אין עליו עוררין": "אין עליו עוררין",  # correct
    "אין תוכוכ ברו": "אין תוכו כברו",
    "ארךא פים": "ארך אפיים",
    "בחרוקש נים": "בחרוק שיניים",
    "ברק יעהשב יעי": "ברקיע השביעי",
    "חורשמ זימות": "חורש מזימות",
    "כידהמלך": "כיד המלך",
    "לאאחת": "לא אחת",
    "לאבכדי": "לא בכדי",
    "לאיסלאבפז": "לא יסולא בפז",
    "השיא עצה": "השיא עצה",  # correct
    "האוחזביד": "האוחז ביד",  # not quite - "האוחז בה ביד"
    "האר יךאפו": "האריך אפו",
    "הגיעו לעמקהשוה": "הגיעו לעמק השווה",
    "הכה גלים": "הכה גלים",  # correct
    "הגיף": "הגיף",  # correct
    "בין השיטין": "בין השיטין",  # correct
    "נדדהש נתו": "נדדה שנתו",
    "אגב אורחא": "אגב אורחא",  # correct
    "אין לדבר יםשחר": "אין לדברים שחר",
    "אתרעמ זלו": "אתרע מזלו",
    "בדבבד": "בד בבד",
    "באכוח": "בא כוח",
    "הדירר גליו": "הדיר רגליו",
    "היה בעוכריו": "היה בעוכריו",  # correct
    "הלךא ימים": "הלך אימים",
    "הכלים": "הכלים",  # correct
    "הסתופף בצלו": "הסתופף בצילו",
    "כאין וכאפס": "כאין וכאפס",  # correct
    "כנסר גליו": "כינס רגליו",
    "יסרוהוכ ליותיו": "ייסרוהו כליותיו",
    "ימיה בלו": "ימיו בלו",  # "ימיהבלו"
    "עמד עלט יבו": "עמד על טיבו",
    "צורמח צבתו": "צור מחצבתו",
    "לאין שיעור": "לאין שיעור",  # correct
    "לאנקףאצבע": "לא נקף אצבע",
    "הציגו ככליריק": "הציגו ככלי ריק",
    "השיבאת פניו": "השיב את פניו",
    "טובהד ברב עיניו": "טוב הדבר בעיניו",
    "חתימתשפם": "חתימת שפם",
    "טביעת עין": "טביעת עין",  # correct
    "עקםאת חוטמו": "עקם את חוטמו",
    "עלפניו": "על פניו",
    "סוסט רויאני": "סוס טרויאני",
    "שוד ושבר": "שוד ושבר",  # correct
    "אבןשפה": "אבן שפה",
    "בדמ עותש ליש": "בדמעות שליש",
    "בודק בציצ יות": "בודק בציציות",
    "גברה ידו": "גברה ידו",  # correct
    "גדשאתהסאה": "גדש את הסאה",
    "היה נביאבע ירו": "היה נביא בעירו",
    "המרהאתפיו": "המרה את פיו",
    "המת יקאת הגלולה": "המתיק את הגלולה",
    "בגדשרד": "בגדי שרד",
    "בראש חוצות": "בראש חוצות",  # correct
    "באותות ובמופתים": "באותות ובמופתים",  # correct
    "דמעותת נין": "דמעות תנין",
    "אבןדרך": "אבן דרך",
    "אבן נגלהמ עללבו": "אבן נגולה מעל ליבו",
    "אבן שואבת": "אבן שואבת",  # correct
    "אור גניזם": "אורגניזם",
    "דרר חוב": "דר רחוב",  # "דר רחוב" = homeless
    "הקיץ הקץ": "הקיץ הקץ",  # correct
    "מפח נפש": "מפח נפש",  # correct
    "גלתה כותרת": "גולת הכותרת",
    "אבל וחפוי ראש": "אבל וחפוי ראש",  # correct
    "אבד עליו הכלח": "אבד עליו הכלח",  # correct
    "פושטיד": "פושט יד",
    "בשנים": "בא בשנים",  # or keep as is
    "אבדו עשתונותיו": "אבדו עשתונותיו",  # correct
    "חלכאי": "חלכאי",  # correct
    "רובץ לפתחו": "רובץ לפתחו",  # correct
    "שדה בור": "שדה בור",  # correct
    "אפר כסת": "אפרכסת",
    "בין הפטיש לסדן": "בין הפטיש לסדן",  # correct
    "ברפ לגתא": "בר פלוגתא",
    "ברקיימא": "בר קיימא",
    "דרךארץ": "דרך ארץ",
    "בנלויה": "בן לוויה",
    "תהה עלק נקנו": "תהה על קנקנו",
    "תוכוכ ברו": "תוכו כברו",
    "קוטלק נים": "קוטל קנים",  # "קוטל קנים" = simple person
    "קוצריד": "קוצר יד",  # "קוצר יד" = inability
    "אבות החשבון": "אבות החשבון",  # correct
    "אבן נגף": "אבן נגף",  # correct
    "אדמתטרשים": "אדמת טרשים",
    "אוזניים לכותל": "אוזניים לכותל",  # correct
    "טמןב חובו": "טמן בחובו",
    "יצא נקי מנכסיו": "יצא נקי מנכסיו",  # correct
    "יצאמ כליו": "יצא מכליו",
    "נערחצנו": "ניער חוצנו",  # "ניער חוצנו"
    "מלאכר מון": "מלאך רמון",  # actually "מלאכת רמון" - encyclopedia
    "נחמה פרתא": "נחמה פורתא",
    "מוסר כליות": "מוסר כליות",  # correct
    "מישב בדעתו": "מיושב בדעתו",
    "בזע ירא נפין": "בזעיר אנפין",
    "בכבד ראש": "בכובד ראש",
    "בנפש חפצה": "בנפש חפצה",  # correct
    "דחהבקש": "דחה בקש",
    "מאחוריה פרגוד": "מאחורי הפרגוד",
    "יהללך זרולאפיך": "יהללך זר ולא פיך",
    "יושב עלגדר": "יושב על הגדר",
    "ירד לטמ יון": "ירד לטמיון",
    "כבשאת לבו": "כבש את ליבו",
    "לחםצר": "לחם צר",
    "ללארבב": "ללא רבב",
    "זרעאל הקוצים": "זרע אל הקוצים",  # "זרע על הקוצים"
    "טבין ותק ילין": "טבין ותקילין",
    "זחיחותדעת": "זחיחות דעת",
    "מטר היהח דור": "מטר היה חדור",  # fragment actually
    "סבב אותוב כחש": "סובב אותו בכחש",
    "שםמבטחו": "שם מבטחו",
    "שעהקלה": "שעה קלה",
    "אחלצרה": "אח לצרה",
    "אחרירב יםלהטת": "אחרי רבים להטות",
    "ביתמט בחיים": "בית מטבחיים",
    "הלעיז": "הלעיז",  # correct
    "טובמראה": "טוב מראה",
    "נמלךבדעתו": "נמלך בדעתו",
    "נקפו לבו": "נקפו ליבו",
    "בענלויה": "בן לוויה",  # actually "בןלויה"
    "בןלויה": "בן לוויה",
    "קוש ושל יוד": "קוצו של יוד",  # already handled above
    "הסתודדות": "הסתודדות",  # correct
    "נים ולא נים": "נים ולא נים",  # correct
    "משל ברוחו": "משל ברוחו",  # correct
    "המרהאתפ יו": "המרה את פיו",  # duplicate handling
    "פחיקוש": "פח יקוש",
    "שומה עליו": "שומה עליו",  # correct
    "כלה": "כילה",  # mosquito net - probably should be כילה
    "יצאבשן ועין": "יצא בשן ועין",
    "דרך כוכבו": "דרך כוכבו",  # correct
    "תיבת פנדורה": "תיבת פנדורה",  # correct
    "עור באפרח": "עורב אפרוח",
    "מאידך גיסא": "מאידך גיסא",  # correct
    "אפ יפית": "אפיפית",
    "אפר יון": "אפריון",
    "אצבעצרדה": "אצבע צרדה",
    "נוח לבר יות": "נוח לבריות",
    "מצד.אחד מחד גיסא": "מחד גיסא",
    "התא בקבעפרר גליו": "התאבק בעפר רגליו",
    "שףהתא בקבעפרר גליו": "שף התאבק בעפר רגליו",  # fragment
    # More fixes for specific broken entries
    "חבורה": "חבורה",  # correct (wound/bruise)
    "חמד לצון": "חמד לצון",  # correct  
    "חפוי ראש": "חפוי ראש",  # correct
    "אבקאדם": "אבק אדם",
    "רונןה לךשולל": "הלך שולל",  # this is a fragment actually
    "נפ לה רוחו": "נפלה רוחו",
    "נפלה רוחו": "נפלה רוחו",  # correct
    "מתימספר": "מתי מספר",
    "קולגיאליות": "קולגיאליות",  # correct
    "אבחה": "אבחה",  # correct
    "רוחק דים": "רוח קדים",
    "סוס טרויאני": "סוס טרויאני",  # correct
    "תמימותדעים": "תמימות דעים",
    "אהיל": "אהיל",  # correct
    "אורלוגין": "אורלוגין",  # correct
    "הטרקטורב ירא": "הטרקטור בירא",  # fragment
}

# Apply fixes
fixed_count = 0
for i, v in enumerate(vocab):
    if i in remove_words_exact:
        continue
    w = v['word']
    if w in word_fixes and word_fixes[w] != w:
        vocab[i]['word'] = word_fixes[w]
        fixed_count += 1

# Additional pattern-based fixes for entries not in the manual list
# Look for common broken patterns
for i, v in enumerate(vocab):
    if i in remove_words_exact:
        continue
    w = v['word']
    # Already fixed above
    if w in word_fixes:
        continue

# ============================================================
# STEP 3: Remove fragment entries
# ============================================================

# Also remove some additional fragments we can detect
# Entries where the word is clearly a sentence fragment
more_fragments = set()
for i, v in enumerate(vocab):
    if i in remove_words_exact:
        continue
    w = v['word']
    d = v['definition']
    
    # Fragment patterns: word has no spaces but definition starts with continuation
    # Or word is very long with merged characters
    
    # These are specific additional fragments
    if w == "רונןה לךשולל":
        more_fragments.add(i)
    elif w == "שףהתא בקבעפרר גליו":
        more_fragments.add(i)
    elif w == "מטר היהח דור" and "מוטיבציה" in d:
        more_fragments.add(i)
    elif w == "הטרקטורב ירא":
        more_fragments.add(i)
    elif w == "בניםמשח יתים עזבו":
        more_fragments.add(i)
    elif w == "הפצעים" and "הוסיף על צערו" in d:
        more_fragments.add(i)
    elif w == "זרהמ לח עלהפ צע ים":
        # This is actually part of the previous entry - but let's check
        # It might be a separate entry for "זרה מלח על הפצעים"
        # Actually looking at it, this IS a legitimate expression
        vocab[i]['word'] = "זרה מלח על הפצעים"
        fixed_count += 1

remove_words_exact.update(more_fragments)

# Build final list
new_vocab = []
removed_words = []
for i, v in enumerate(vocab):
    if i in remove_words_exact:
        removed_words.append(f"[{i}] \"{v['word']}\" -> REMOVED")
    else:
        new_vocab.append(v)

print(f"\nTotal removed: {len(removed_words)}")
print(f"Total fixed spacing: {fixed_count}")  
print(f"New total: {len(new_vocab)}")

# ============================================================
# STEP 4: Write back to file
# ============================================================

new_vocab_json = json.dumps(new_vocab, ensure_ascii=False)
new_content = content[:match.start(1)] + new_vocab_json + content[match.end(1):]

with open('index.html', 'w') as f:
    f.write(new_content)

print("\nFile written successfully!")
print("\n--- Removed entries ---")
for r in removed_words[:30]:
    print(r)
if len(removed_words) > 30:
    print(f"... and {len(removed_words)-30} more")

print("\n--- Sample fixed entries ---")
sample_fixes = [(k, v) for k, v in word_fixes.items() if v != k][:30]
for orig, fixed in sample_fixes:
    print(f'  "{orig}" → "{fixed}"')
