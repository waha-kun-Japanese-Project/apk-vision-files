"""
Problem information database - Base knowledge for recommendations.
"""

import json
from typing import Dict, Any, List

# Base knowledge - will be used as seed for RAG and fallback
PROBLEM_INFO = {
    "Pipe_Damage": {
        "arabic": "تلف في أنبوب المياه",
        "recommendation": "يوصى بإيقاف مصدر المياه فوراً ثم إصلاح أو استبدال الجزء التالف من الأنبوب.",
        "explanation": """
تم رصد علامات تلف في الأنبوب، مثل: تشققات، كسور، أو تسرب للمياه.
ا.
""",
        "steps": [
            "إيقاف مصدر المياه.",
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
        "recommendation": "تقليل كمية المياه وتنظيم عملية الري مع فحص القنوات.",
        "explanation": """
تم رصد تجمع كبير للمياه أو خروجها عن المسار الطبيعي.
قد يكون السبب زيادة ضخ المياه أو خلل في شبكة الري أو انسداد جزئي.
""",
        "steps": [
            "تقليل ضخ المياه.",
            "فحص القناة.",
            "إزالة أي انسداد.",
            "إعادة اختبار تدفق المياه.",
            "متابعة المنطقة."
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
        "recommendation": "تنظيف قناة الري وإزالة الرواسب أو المخلفات.",
        "explanation": """
تم رصد عائق داخل قناة الري يمنع تدفق المياه.
قد يكون العائق عبارة عن طين أو رمال أو نباتات أو مخلفات متراكمة.
""",
        "steps": [
            "فحص قناة الري.",
            "إزالة الرواسب.",
            "تنظيف القناة.",
            "التأكد من عودة تدفق المياه.",
            "إجراء صيانة دورية."
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
