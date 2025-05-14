var toastList = document.querySelector('.toasts');

// Sử dụng vòng lặp để lặp qua danh sách toast từ Django template
var toastElements = document.querySelectorAll('.toasts .toast');

toastElements.forEach(function(toastElement) {
    // Gọi hàm để đặt giới hạn thời gian cho mỗi toast
    setToastTimeout(toastElement);
});

function setToastTimeout(toastElement) {
    // Đặt giới hạn thời gian hiển thị của toast
    setTimeout(function() {
        toastElement.style.animation = 'slideHide 1.5s ease forwards';

        // Xóa toast sau khi hoàn thành hiệu ứng animation
        setTimeout(function() {
            toastElement.remove();
        }, 1500);
    }, 5000); // Đặt giới hạn thời gian hiển thị là 5 giây
}
