from datetime import datetime
import json
from django.shortcuts import render

from home.calculations import calculate_daily_products_sold, calculate_day_revenue, calculate_monthly_products_sold, calculate_month_revenue, calculate_users_registered_this_month, count_registered_users_today, get_revenue_data_for_chart


# Create your views here.
def index(request):

    doanhThuNgay = calculate_day_revenue()
    doanhThuThang = calculate_month_revenue()
    sanPhamBanThang = calculate_monthly_products_sold()
    sanPhamBanNgay = calculate_daily_products_sold()
    userDKNgay = count_registered_users_today()
    userDKThang = calculate_users_registered_this_month()
    #BIỂU ĐỒ DOANH THU THEO NĂM
    current_year = datetime.now().year 
    chart_data = get_revenue_data_for_chart(current_year)

    context = {
        'doanhThuThang': doanhThuThang,
        'sanPhamBanThang' : sanPhamBanThang,
        'sanPhamBanNgay': sanPhamBanNgay,
        'doanhThuNgay'    : doanhThuNgay,
        'userDKThang'    : userDKThang,
        'userDKNgay'    : userDKNgay,
        'chart_data': json.dumps(chart_data),
        'userDKNgay' : userDKNgay

        }
    return render(request, 'pages/index.html', context)