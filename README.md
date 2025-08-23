Image Analysis with Python
================================

[![Stand With Ukraine](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner-direct-single.svg)](https://stand-with-ukraine.pp.ua)

_Bioinformatics for Ukraine workshop, xx-xx October 2025, Kyiv, Ukraine._

---

# Структура і зміст курсу

Курс має декілька незалежних цілей:

- Зрозуміти загальні матоди та бібліотеки для роботи із цифровими зображеннями з використанням python.
- Вивчити/пригадати загальні підходи для роботи з кодом на python для його ефективного повторного використання.
- Знайомство із [napari](https://napari.org/stable/), python-based програми для відображення і обробки зображень.

Основним форматом завдань для самостійної роботи буде перетворення пройденого на занятті матеріалу у набір зручних саме для вас інструментів. Упаковка окремих етапів обробки чи аналізу зображень в функції, функцій в модулі чи класи, а модулів в пакети. В залежності від рівня студентів ми можемо не встигнути пройти всі зазначені рівні. Але з точки зору навичок програмування в цьому курсі буде акцент саме на створені інструментів, а не одноразових скриптів чи ноутбуків.

До початку курсу для слухачів було б дуже добре знати/пригадати загальний синтаксис python. Типи даних (`str`, `int`, `float`, `list`, `dict`, `bool`, etc.) та основні оператори і синтаксичні конструкції (`if-else`, `for loop`).

> [!TIP]
> Типи даних в Python [українською](https://w3schoolsua.github.io/python/python_datatypes.html#gsc.tab=0) або [англійською](https://www.w3schools.com/python/python_datatypes.asp).

> [!TIP]
> Cинтаксис конструкцій [if-else](https://w3schoolsua.github.io/python/python_conditions.html#gsc.tab=0) та [for loop](https://w3schoolsua.github.io/python/python_for_loops.html#gsc.tab=0) українською й [if-else](https://www.w3schools.com/python/python_conditions.asp) та [for loop](https://www.w3schools.com/python/python_for_loops.asp) англійською.

> [!TIP]
> Cинтаксис функцій та класів в Python [українською](https://w3schoolsua.github.io/python/python_functions.html#gsc.tab=0) або [англійською](https://www.w3schools.com/python/python_functions.asp).

| Вступна зустріч          | Огляд загальної структури курсу, огляд матеріалів курсу і підготовка до роботи (за потреби допомога із встановлення IDE, створенням робочих оточень, встановлення бібліотек тощо). |
| ------------------------ | ------------------------------------------------------------ |
| **Практичні заняття**    | 4x заняття по 1.5 години: 15-20 хв короткий вступ, 30-40 хв пояснення матеріалу заняття, решта часу на практичну роботу. Окремий Jupyter-ноутбук для кожної зустрічи містить частину із поясненням та прикладами, частину для практичної роботи і домашні завдання. |
| **Підготовка "проєкту"** | По завершенню практичних занять пропоную впродовж тижня продовжити самостійно працювати, щоб побудувати на основі отриманих навичок корисний особисто для себе набір інструментів для аналізу зображень, оформлення його у вигляді плагіну napari. |

## Зміст зустрічей

| # | Bio | Py              | Homework      | Lib            |
| ------ | -------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 0 | Огляд підходів оптичної мікроскопії та даних, що отримуються на міксрокопах. | Встановлення IDE, створення оточень та встановлення необхідних бібліотек. |  | pip |
| 1 | Зображення як багатовимірні масиви, відображення багатоканальних і тривимірних зображень, псевдокольори (color maps / lookup table). | Завантаження/збереження зображень, маніпуляції з масивами numpy, відображення зображень. |  | jupyter, numpy, matplotlib |
| 2 | Попередня обробка зображень, детекція та сегментація об'єктів на зображенях. | Фільтрація зображень, методи побудови бінарних і багаторівневих масок, морфологічні операції над масками. Функції. |  | scikit-image, scipy, ndimage |
| 3 | Отримання кількісних даних з зображень та збереження результатів аналізу. | Оцінка морфологічних параметрів параметрів масок, оцінка зміни параметрів в масках в часі, збреження результатів аналізу в табличному форматі. Модулі/класи. |  | scikit-image, scipy pandas |
| 4 | napari -  open source для переглядання і аналізу зображень | Пробуємо упакувати результати роботи у модулі та перетворити їх у плагін для  napari. Пакети python. |  | napari |

---

# Підготовка до роботи

#### Необхідні бібліотеки
- Python
- Jupyter
- Numpy
- Pandas
- Scipy
- Scikit-image
- Matplotlib

> [!TIP]
> Основи роботи з масивами NumPy [українською](https://devzone.org.ua/post/chomu-vam-slid-vykorystovuvaty-numpy) або [англійською](https://numpy.org/doc/stable/user/absolute_beginners.html).

Наполегливо рекомендую використовувати менеджер оточень для встановлення бібліотек щоб запобігти конфлікту версій та залежностей ([Miniconda](https://docs.conda.io/en/latest/miniconda.html), [venv](https://docs.python.org/3/library/venv.html) і т.д.), інструкція для роботи з Conda наведена нижче.

#### Встановлення Conda та створення оточення
[Встановіть](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) __Miniconda__ для Вашої операційної системи.

> [!WARNING]
> Рекомендую встановлювати саме Miniconda, оскільки Anaconda одразу містить багато непотрібних для проекту бібліотек і важить > 2GB.

Наступні команди вводити в Unix-термінал (у випадку Linux або MacOS) або Anaconda Prompt (у випадку Windows).

Створення оточення з мінімальним набором бібілотек:
```
conda create -n bioin-img-env python>3.9 jupyter numpy matplotlib pandas
```

Запуск оточення:
```
conda activate bds3-img-env
```

Вихід з оточення:
```
conda deactivate bds3-img-env
```

Створення повного оточення з YAML файла:
```
conda env create -f bds3-img-env.yml
```

#### Встановлення napari
[napari](https://napari.org/stable/) є відкритою бібліотекою для візуалізацію та аналізу багатовимірних зображень. Окрім можливості використання napari надає зручний графічний інтерфейс та простий framework для інтеграції нового фукціоналу у вигляді плагінів. Доступні плагіни можна знайти на [napari-hub](https://www.napari-hub.org/).

Встановлення за допомогою `pip` через Unix-термінал/Anaconda Prompt, встановлювати слід в оточенні __bds3-img-env__:
```
python -m pip install "napari[all]"
```

Для запуска графічного інтерфейса виконайте команду ```napari``` в Unix-терміналі/Anaconda Prompt в оточені __bds3-img-env__.

> [!TIP]
> До початку курсу рекомендую ознайомитись з  матеріалами [napari how-to guides](https://napari.org/stable/howtos/index.html).


## Встановлення IDE

Інтегроване середовище розробки (Integrated Development Environment - IDE) значно спростить роботу з оточенями Conda та Jupyter-ноутбуками з яких складається даний курс.

Встановлення та налаштування:
- [Встановіть](https://code.visualstudio.com/) __Visual Studio Code__ відповідно Вашій оперційній системі
- Для роботи з кодом Python та Jupyter-ноутбуками користуючись вкладкою _Розширення_ (_Extensions_) на лівій панелі IDE встановіть розширення __Python__ та __Jupyter__
- Для запуску Jupyter-ноутбука в середовищі Conda натисніть на меню _Select Kernel_ у верхньому правому кутку вікна відкритого Jupyter-ноутбука, оберіть пункт _Python Environment_ та необхідне нам оточеня  __bioin-img-env__ серед запропонованих варіантів інтерпретаторів чи оточень (у випадку такого підключення запуск оточення через Unix-термінал/Anaconda Prompt не потрібен)


## Обліковий запис PyPI (optional)

Створення облікового запису [Python Package Index](https://pypi.org/) (PyPI) дозволить розповсюджувати і встановлювати створені Вами бібліотеки та плагіни napari за допомогою системи керування пакетами pip.

#### Додаткові бібліотеки для збірки та публікації бібліотек:
- setuptools >= 61.0
- build
- twine

---

# Матеріали до курсу

## Корисні посилання

- [Scikit-image examples](https://scikit-image.org/docs/stable/auto_examples/index.html)
- [Image processing learning resorces](https://homepages.inf.ed.ac.uk/rbf/HIPR2/hipr_top.htm)
- [The Carl Zeiss Microscopy Online Campus](https://zeiss-campus.magnet.fsu.edu/index.html)
- [Scientific Volume Imaging](https://svi.nl/Huygens-Imaging-Academy)
- [Introduction to Modeling for Neuroscience](https://dabane-ghassan.github.io/ModNeuro/)
- [Convolutions in image processing, YouTube](https://www.youtube.com/watch?v=8rrHTtUzyZA)


## Література

- [Fundamentals of Fluorescence Imaging](https://www.taylorfrancis.com/books/edit/10.1201/9781351129404/fundamentals-fluorescence-imaging-guy-cox)
- [Imaging Cellular and Molecular Biological Functions](https://link.springer.com/book/10.1007/978-3-540-71331-9)
- [Handbook of Biological Confocal Microscopy](https://link.springer.com/book/10.1007/978-0-387-45524-2)
- [An introduction to optical super-resolution microscopy for the adventurous biologist](https://www.researchgate.net/publication/323073291_An_introduction_to_optical_super-resolution_microscopy_for_the_adventurous_biologist)
- [Nanoscopy and Multidimensional Optical Fluorescence Microscopy](https://www.tandfonline.com/doi/pdf/10.1080/00107514.2011.580375)

 <p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/wisstock/BioIn_2025_img_analysis">Image analysis with python, workshop for BioInUA </a> by <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://github.com/wisstock">Borys Olifirov</a> is licensed under <a href="https://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="_blank" rel="license noopener noreferrer" style="display:inline-block;">CC BY 4.0<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1" alt=""><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1" alt=""></a></p> 