    const dropdown = document.querySelector('.dropdown__btn');
    const options = document.querySelectorAll('.dropdown__option');
    const textBtn = document.querySelector('.dropdown__btn-text');

    dropdown.addEventListener('click', () => {
      dropdown.classList.toggle('active');
    })

    options.forEach(option => {
      option.addEventListener('click', () => {
        let selectedOption = option.innerText;
        textBtn.textContent = selectedOption;

        dropdown.classList.remove('active');
      })
    })