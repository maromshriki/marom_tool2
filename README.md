# platform-cli (marom_tool)

CLI לניהול משאבי AWS (EC2, S3, Route53) תוך אכיפת כללים: תגיות חובה, מגבלות, ואבטחה.
הכלי מתייג כל משאב עם:
- `CreatedBy=platform-cli`
- `Owner=<username>` (ניתן להעביר דרך `--owner`, ברירת מחדל היא שם המשתמש במכונה).

## התקנה
```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## הרצה מהירה
כל הפקודות מקבלות `--profile` ו-`--region` (ברירת מחדל: region מ־AWS config).
```bash
python maromtool.py --help
```

### EC2
- יצירה (רק t3.micro / t2.small; מגבלה: עד 2 רצות שנוצרו ע״י ה־CLI)
```bash
python maromtool.py --profile <aws_profile> ec2 create --type t3.micro --os ubuntu
```
- התחלה/עצירה (רק לאינסטנסים של ה־CLI)
```bash
python maromtool.py ec2 start --id i-0123456789abcdef0
python maromtool.py ec2 stop  --id i-0123456789abcdef0
```
- רשימה (רק אינסטנסים של ה־CLI)
```bash
python maromtool.py ec2 list
```

### S3
- יצירת דלי (private כברירת מחדל). אם public — חובה אישור מפורש.
```bash
python maromtool.py s3 create --name my-cli-bucket-123 --public --confirm yes
```
- העלאת קובץ (רק לדליים של ה־CLI)
```bash
python maromtool.py s3 upload --bucket my-cli-bucket-123 --key path/in/bucket/file.txt --file ./file.txt
```
- רשימה (רק דליים של ה־CLI)
```bash
python maromtool.py s3 list
```

### Route53
- יצירת Hosted Zone
```bash
python maromtool.py route53 create-zone --name example.com.
```
- יצירה/עדכון רשומה (רק ב־Hosted Zone של ה־CLI)
```bash
python maromtool.py route53 upsert-record --zone-id Z123ABC --name www.example.com. --type A --ttl 300 --values 1.2.3.4
```
- מחיקת רשומה
```bash
python maromtool.py route53 delete-record --zone-id Z123ABC --name www.example.com. --type A --values 1.2.3.4
```
- רשימה (זונות/רשומות של ה־CLI בלבד)
```bash
python maromtool.py route53 list-zones
python maromtool.py route53 list-records --zone-id Z123ABC
```

## אבטחה
- אין סודות בקוד. השתמשו ב־AWS profiles/roles.
- הודעות שגיאה קריאות ופלט מסכם לכל פעולה.
