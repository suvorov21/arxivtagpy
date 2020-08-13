import setuptools

setuptools.setup(
    name='arXivTag',
    version='0.1',
    author="Sergey",
    author_email="suvorov a_t inr ru",
    packages=setuptools.find_packages(),
    python_requires='>=3.6',
    install_requires=[
        'flask',
        'flask_cors',
        'requests',
        'feedparser'
    ],
    )