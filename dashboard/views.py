from datetime import datetime
from django.shortcuts import render

from home.calculations import calculate_daily_products_sold, calculate_day_revenue, calculate_monthly_products_sold, calculate_month_revenue, calculate_users_registered_this_month, count_registered_users_today, get_revenue_chart, get_revenue_line_chart


# Create your views here.
def index(request):

    doanhThuNgay = calculate_day_revenue()
    doanhThuThang = calculate_month_revenue()
    sanPhamBanThang = calculate_monthly_products_sold()
    sanPhamBanNgay = calculate_daily_products_sold()
    userDKNgay = count_registered_users_today()
    userDKThang = calculate_users_registered_this_month()
    #BIỂU ĐỒ DOANH THU THEO NĂM
    current_year = current_year = datetime.now().year 
    revenue_chart_html = get_revenue_chart(current_year)
    revenue_line_chart_html = get_revenue_line_chart(current_year)

    print('doanhThuNgay: ', doanhThuNgay),
    print('doanhThuThang: ', doanhThuThang),
    print('sanPhamBanThang: ', sanPhamBanThang),
    print('sanPhamBanNgay: ', sanPhamBanNgay),
    print('userDKNgay: ', userDKNgay),
    print('userDKThang: ', userDKThang),


    context = {
        'doanhThuThang': doanhThuThang,
        'sanPhamBanThang' : sanPhamBanThang,
        'sanPhamBanNgay': sanPhamBanNgay,
        'doanhThuNgay'    : doanhThuNgay,
        'userDKThang'    : userDKThang,
        'userDKNgay'    : userDKNgay,
        'revenue_chart_html'   : revenue_chart_html,
        'revenue_line_chart_html'   : revenue_line_chart_html,
        'userDKNgay' : userDKNgay

        }
    return render(request, 'pages/index.html', context)