# Data-bench (Defensive Domain Breach Monitor)

> เครื่องมือนี้ออกแบบเพื่อ **งานป้องกัน** เท่านั้น: ใช้ตรวจสอบโดเมนที่คุณมีสิทธิ์ดูแลว่ามีสัญญาณข้อมูลรั่วจากแหล่งข่าวสาธารณะหรือไม่

## แนวคิด

ระบบรับ `URL` แล้วแปลงเป็น `domain` จากนั้นยิงเช็กกับแหล่งข้อมูล breach intelligence แบบถูกกฎหมาย (เช่น API ที่อนุญาตให้ค้นหาโดเมนที่ยืนยันสิทธิ์แล้ว) และรวมผลให้อ่านง่าย

- Input: `https://example.com/login`
- Normalize: `example.com`
- Query sources: HIBP Domain API (ถ้ามี key), local/demo feed
- Aggregate: จำนวน incident, severity, แนะนำการตอบสนอง

## ข้อควรระวังทางกฎหมายและจริยธรรม

- ใช้เฉพาะโดเมนที่มีสิทธิ์เท่านั้น
- ไม่ดึงข้อมูลจากเว็บมืด/แหล่งผิดกฎหมาย
- ไม่แสดงข้อมูลละเอียดที่เป็นความลับของเหยื่อโดยไม่จำเป็น
- เก็บ log และสิทธิ์การเข้าถึงตาม PDPA/GDPR

## การใช้งาน

```bash
python3 monitor.py --url https://example.com --demo-data data/demo_breaches.json
```

ตัวอย่างเปิด HIBP (ต้องมี API key):

```bash
HIBP_API_KEY=your_key python3 monitor.py --url https://example.com --enable-hibp
```

## รูปแบบผลลัพธ์

โปรแกรมพิมพ์ JSON ที่มี:

- `target_domain`
- `total_incidents`
- `max_severity`
- `sources`
- `recommendations`

## โครงสร้างไฟล์

- `monitor.py` — ตัวหลักสำหรับ normalize URL, query feeds, aggregate
- `data/demo_breaches.json` — demo intelligence feed

