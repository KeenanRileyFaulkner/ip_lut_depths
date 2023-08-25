IN_ENV = if [ -e .venv/bin/activate ]; then . .venv/bin/activate; fi;

install: venv rapidwright requirements

venv:
	python -m venv .venv
	$(IN_ENV) python -m pip install -U pip

rapidwright:
	mkdir -p third_party && cd third_party && git clone https://github.com/Xilinx/RapidWright.git && cd RapidWright && ./gradlew compileJava && export PATH=`pwd`/bin:$PATH && source bin/rapidwright_classpath.sh && cd ../..

requirements:
	$(IN_ENV) python -m pip install -r requirements.txt