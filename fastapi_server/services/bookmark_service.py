from schemas.bookmark_schema import bookmarkCreate, bookmarkResponse
from typing import List

bookmarks = []
bookmark_id = 1


def create_bookmark(bookmark: bookmarkCreate) -> bookmarkResponse:
    
    global bookmark_id
    
    new_bookmark = {
        "id": bookmark_id,
        "title": bookmark.title,
        "url": bookmark.url,
        "description": bookmark.description,
        
    }
    
    bookmarks.append(new_bookmark)
    bookmark_id += 1
    
    return new_bookmark


def get_bookmarks() -> List[bookmarkResponse]:
    return bookmarks

