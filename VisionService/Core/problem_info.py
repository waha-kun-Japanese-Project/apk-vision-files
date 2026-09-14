"""
Problem information database - Base knowledge for recommendations.
"""

import json
from typing import Dict, Any, List

PROBLEM_INFO = {
    "Pipe_Damage": {
        "arabic": "تلف في أنبوب المياه",
        "recommendation": "يوصى بإيقاف مصدر المياه فوراً ثم إصلاح أو استبدال الجزء التالف من الأنبوب.",
        "explanation": "تم رصد علامات تلف في الأنبوب، مثل: تشققات، كسور، أو تسرب للمياه.",
        "steps": [
            "أوقف المياه فوراً.",
            "تحديد مكان التلف.",
            "فحص الأنبوب بالكامل.",
            "استبدال أو إصلاح الجزء التالف.",
            "إعادة تشغيل المياه.",
            "اختبار شبكة الري.",
            "التأكد من عدم وجود أي تسرب."
        ],
        "severity_factors": {
            "critical": "تلف في الأنبوب الرئيسي أو تسرب كبير",
            "high": "تلف في أنبوب فرعي مع تسرب مستمر",
            "medium": "تلف بسيط مع تسرب بطيء",
            "low": "تشققات سطحية بدون تسرب"
        }
    },
    "Overflow": {
        "arabic": "فيض في المياه",
        "recommendation": "خفف ضخ المية على طول، وتأكد إن القناة مش مسدودة.",
        "explanation": "تم رصد تجمع كبير للمياه أو خروجها عن مكانها الطبيعي.",
        "steps": [
            "خفف ضخ المية من المضخة.",
            "افحص القناة وشوف لو في حاجة سادة المية.",
            "لو في انسداد، نضفه بإيدك أو باستخدام عصا طويلة.",
            "بعد التنضيف، شغل المية تاني.",
            "لو الفيض رجع، حاول تخفيف الضخ."
        ],
        "severity_factors": {
            "critical": "فيض يهدد المحاصيل أو الممتلكات",
            "high": "فيض يؤثر على مساحة كبيرة من المزرعة",
            "medium": "فيض في منطقة محدودة",
            "low": "تجمع بسيط للمياه"
        }
    },
    "Blockage": {
        "arabic": "انسداد في قناة الري",
        "recommendation": "افحص القناة وشوف مكان الانسداد، ونظفه بنفسك.",
        "explanation": "تم رصد عائق داخل قناة الري يمنع تدفق المياه.",
        "steps": [
            "افحص القناة وشوف مكان الانسداد.",
            "لو طين أو رمال، نضفه بإيدك أو باستخدام مجرفة.",
            "لو نباتات، اقطعها واسحبها بره القناة.",
            "بعد التنضيف، شغل المية وتأكد إن المية رجعت.",
            "لو الانسداد بيتكرر، نظف القناة كل شهر."
        ],
        "severity_factors": {
            "critical": "انسداد كامل يوقف الري",
            "high": "انسداد جزئي يقلل التدفق بشكل كبير",
            "medium": "انسداد بسيط يؤثر على جزء من القناة",
            "low": "رواسب بسيطة لا تؤثر على التدفق"
        }
    }
}

def get_knowledge_documents() -> List[Dict[str, Any]]:
    """Convert PROBLEM_INFO to documents for RAG vector store."""
    documents = []
    for problem_type, info in PROBLEM_INFO.items():
        doc = {
            "page_content": f"""
Problem Type: {problem_type}
Arabic Name: {info['arabic']}
Recommendation: {info['recommendation']}
Explanation: {info['explanation']}
Steps: {', '.join(info['steps'])}
Severity Factors: {json.dumps(info['severity_factors'], ensure_ascii=False)}
""",
            "metadata": {
                "problem": problem_type,
                "arabic": info['arabic'],
                "severity_factors": info['severity_factors']
            }
        }
        documents.append(doc)
    return documents
