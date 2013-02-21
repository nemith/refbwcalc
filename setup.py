#!/usr/bin/env python
from distutils.core import setup
from refbwcalc import get_version

setup(
	name='refbwcalc',
	version=get_version(),
	description="Script to calculate the resulting OSPF metrics for different"\
	            "autobw settings",
	author='Brandon Bennett',
	author_email='bennetb@gmail.com',
	license='BSD',
	packages=['refbwcalc'],
	scripts=['bin/refbwcalc'])