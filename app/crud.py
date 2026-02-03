from .models import Document
from sqlalchemy.future import select

async def save_document(db, doc: Document):
    db.add(doc)
    await db.commit()

async def get_docs_for_user(db, user_id, tenant_id, groups):
    q = await db.execute(select(Document).where(Document.tenant_id == tenant_id))
    return q.scalars().all()
