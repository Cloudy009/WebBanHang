document.querySelectorAll('.nav-link').forEach
(
  function (navItem) 
  {
    navItem.addEventListener('click', function() 
    {
      // Xóa lớp 'active' khỏi tất cả các mục điều hướng
      document.querySelectorAll('.nav-link').forEach
      (
        function(item)
        {
          item.classList.remove('active');
        }
      );
      // Thêm lớp 'active' vào mục điều hướng được click
      this.classList.add('active');
    });
  }
);