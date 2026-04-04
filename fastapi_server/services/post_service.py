from schemas.post_schema import PostCreate, PostResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from models.post_model import Post

def create_post(db: Session, post: PostCreate) -> Post:
    
    new_post = Post(
        title=post.title,
        content=post.content
    )
        
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return new_post
    

#tool용 함수 준비
def count_posts(db: Session) -> int:
    stmt = select(func.count()).select_from(Post)
    return db.scalar(stmt) or 0

def get_post_by_id(db:Session, post_id: int) -> Post | None:
    stmt = select(Post).where(Post.id == post_id)
    return db.scalar(stmt)



    