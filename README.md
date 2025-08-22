מעולה 🙌 הנה גרסה מלאה של README.md שתוכל לשים בריפו שלך, עם הוראות התקנה ושימוש צעד-אחר-צעד (כולל aws configure):

# marom_tool – AWS CLI Tool

כלי CLI לניהול משאבי AWS (EC2, S3, Route53) עם מגבלות ותקני אבטחה.  
הכלי נבנה באמצעות `boto3` ומאפשר יצירה, ניהול ורשימה של משאבים, תוך שימוש בתגיות לזיהוי (CreatedBy=platform-cli, Owner=<username>).

---

## דרישות מקדימות
1. Python 3.9+
2. חשבון AWS עם הרשאות מתאימות (EC2, S3, Route53).
3. התקנת AWS CLI:  
   ```bash
   pip install awscli


הגדרת פרטי ההתחברות שלך פעם אחת:

aws configure


תתבקש להזין:

AWS Access Key ID

AWS Secret Access Key

Default region (למשל: us-east-1)

Default output format (למשל: json)

ההגדרות נשמרות תחת ~/.aws/credentials ו־~/.aws/config.

התקנה
git clone https://github.com/maromshriki/marom_tool.git
cd marom_tool

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

שימוש

הסינטקס הכללי:

python maromtool.py [--profile PROFILE] <resource> <action> [options]

EC2

יצירת אינסטנס (רק t3.micro או t2.small, עם מגבלה של 2 אינסטנסים):

python maromtool.py ec2 create --type t3.micro --os ubuntu


עצירת אינסטנס (רק אינסטנסים מתויגים ע"י ה־CLI):

python maromtool.py ec2 stop --id i-1234567890abcdef


הפעלה מחדש:

python maromtool.py ec2 start --id i-1234567890abcdef


רשימת אינסטנסים:

python maromtool.py ec2 list

S3

יצירת דלי פרטי:

python maromtool.py s3 create --name my-cli-bucket


יצירת דלי ציבורי (נדרשת אישור מפורש):

python maromtool.py s3 create --name my-public-bucket --public --confirm yes


העלאת קובץ:

python maromtool.py s3 upload --bucket my-cli-bucket --key foo.txt --file ./foo.txt


רשימת דליים:

python maromtool.py s3 list

Route53

יצירת Hosted Zone:

python maromtool.py route53 create-zone --name example.com.


יצירת רשומת A:

python maromtool.py route53 create-record --zone-id Z12345 --name www.example.com. --type A --value 1.2.3.4


עדכון רשומה:

python maromtool.py route53 update-record --zone-id Z12345 --name www.example.com. --type A --value 5.6.7.8


מחיקת רשומה:

python maromtool.py route53 delete-record --zone-id Z12345 --name www.example.com. --type A


רשימת רשומות:

python maromtool.py route53 list-records --zone-id Z12345

הערות

הכלי לא שומר סודות ב־repo. ההזדהות מתבצעת באמצעות aws configure או ע"י פרופילים קיימים.

תגיות זהות נוספות:

CreatedBy=platform-cli

Owner=<username> (מוגדר אוטומטית ע"פ getpass.getuser())

עזרה
python maromtool.py --help
python maromtool.py ec2 --help
python maromtool.py s3 --help
python maromtool.py route53 --help
