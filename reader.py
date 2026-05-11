"""Sarvam Form Reader — extract structured data from Indian government forms."""
import os, json, base64, sys
from pathlib import Path
from dotenv import load_dotenv
from sarvamai import SarvamAI
from rich.console import Console
from rich.panel import Panel

load_dotenv()
console=Console()
client=SarvamAI(api_subscription_key=os.environ["SARVAM_API_KEY"])
FORM_FIELDS={"aadhaar":["name","dob","gender","address","aadhaar_number"],"ration":["card_number","head_of_family","members","address"],"generic":["all_fields"]}

def extract(path):
    with open(path,"rb") as f: data=base64.b64encode(f.read()).decode()
    ext=Path(path).suffix.lstrip(".").lower()
    return client.documents.parse(document={"type":"base64","media_type":"application/pdf" if ext=="pdf" else f"image/{ext}","data":data}).text

def process(path, form_type="generic", output="form_data.json"):
    raw=extract(path)
    lang=client.text.identify_language(input=raw[:300]).language_code
    translated=raw if lang=="en-IN" else client.text.translate(input=raw,source_language_code=lang,target_language_code="en-IN").translated_text
    fields=FORM_FIELDS.get(form_type,["all_fields"])
    r=client.chat.completions(messages=[
        {"role":"system","content":f"Extract these fields as JSON: {fields}. Return only JSON."},
        {"role":"user","content":translated}],model="sarvam-m")
    try: structured=json.loads(r.choices[0].message.content)
    except: structured={"raw":r.choices[0].message.content}
    result={"source":path,"language":lang,"form_type":form_type,"extracted_fields":structured}
    with open(output,"w",encoding="utf-8") as f: json.dump(result,f,ensure_ascii=False,indent=2)
    console.print(Panel(json.dumps(structured,ensure_ascii=False,indent=2),title="Extracted Fields"))
    console.print(f"[green]Saved to {output}[/green]")

if __name__=="__main__":
    process(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else "generic",sys.argv[3] if len(sys.argv)>3 else "form_data.json")
