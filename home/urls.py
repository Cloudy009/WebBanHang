from django.urls import include, path, re_path
from home import views

urlpatterns = [
    path('', views.home2, name='homePage'),

    path('get_cart_items/', views.get_cart_items, name='get_cart_items'),
    path('get-cart-items-empty/', views.get_empty_cart_data, name='get_empty_cart_items'),

    path('check-user-distance/', views.check_user_distance, name='check_user_distance'),
    path('get-address-from-coordinates/', views.get_address_from_coordinates, name='get_address_from_coordinates'),
    path('apply_voucher/', views.apply_voucher, name='apply_voucher'),

    path('add_to_cart/', views.add_to_cart, name='add_to_cart'),
    path('remove_item/', views.remove_item, name='remove_item'),
    path('like/', views.like_product, name='like_product'),
    path('favorites/', views.favorite_products, name='favorite_products'),
    path('remove_favorite/', views.remove_favorite, name='remove_favorite'),
    path('profile/', views.infor_profile, name='profile'),
    path('update_cart/', views.update_cart, name= 'update_cart'),
    path('admin/', views.index, name= 'index'),
    path('send_email/', views.send_email, name= 'send_email'),
    path('cart/', views.view_cart, name= 'cart_Page'),
    path('test/', views.testFiller, name= 'test'),
    path('cart/checkOut/', views.checkOut, name= 'checkOut'),
    path('cart/thanhToan/', views.thanhToan, name='thanhToan'),
    path('order/confirmation/<int:hoadon_id>/', views.order_confirmation, name='order_confirmation'),
    path('infor/', views.inforCustomer, name= 'inforCustomer'),
    path('dashboard/', views.dashboard, name= 'dashboard'),
    path('dashboard/confirm_receipt/', views.confirm_receipt, name='confirm_receipt'),

    path('update-contact-info/', views.update_contact_info, name='update_contact_info'),

    path('product_review/<int:product_id>/<int:hoadon_id>/', views.product_review, name='product_review'),
    path('add_review/<int:product_id>/<int:hoadon_id>/<int:detail_id>/', views.add_review, name='add_review'),
    path('products/', views.product_list, name='product_page'),
    path('products/category/<int:category_id>/', views.product_list, name='product_page_by_category'),  # With category ID
    path('search_products/', views.search_products, name='search_products'),
    path('product_detail/<str:identifier>/', views.product_detail, name='product-detail'),
    path('payment', views.payment, name='payment'), # type: ignore

   
    re_path(r'^payment_ipn$', views.payment_ipn, name='payment_ipn'),
    re_path(r'^payment_return$', views.payment_return, name='payment_return'),
    re_path(r'^query$', views.query, name='query'),
    re_path(r'^refund$', views.refund, name='refund'),
]



