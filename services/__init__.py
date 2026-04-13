import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.auth_service import authenticate_user, create_jwt, register_user
from services.book_service import (
    create_author,
    create_book,
    create_genre,
    delete_author,
    delete_book,
    delete_genre,
    get_author_by_id,
    get_book_by_id,
    get_book_detail,
    get_genre_by_id,
    get_low_stock_count,
    get_total_books_count,
    list_authors,
    list_books,
    list_genres,
    update_author,
    update_book,
    update_genre,
)
from services.cart_service import (
    add_to_cart,
    clear_cart,
    get_cart,
    get_cart_count,
    remove_cart_item,
    update_cart_item,
)
from services.order_service import (
    check_stock_availability,
    create_order,
    get_all_orders,
    get_order_detail,
    get_user_orders,
    update_order_status,
)
from services.review_service import (
    create_review,
    delete_review,
    get_book_average_rating,
    get_book_review_count,
    get_book_reviews,
    get_review_by_id,
    update_review,
    user_has_reviewed_book,
)