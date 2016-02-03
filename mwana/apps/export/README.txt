HOW TO ADD APP TO MWANA

1. Clone mwana. Follow the steps on https://github.com/mwana/mwana
2. Copy the folder export to mwana/mwana/apps/
3. Add the app to mwana by adding this line 
	INSTALLED_APPS.append("mwana.apps.export") 
	to 	
	mwana/mwana/zambia/settings_country.py
4. Add the this line
	(r'^exportjson/', include('mwana.apps.export.urls')),
	to
	mwana/mwana/urls.py in urlpatterns variable
5. Run mwana ./manage.py runserver
6. get the turnaround export json data by entering the url:
	http://127.0.0.1:8000/exportjson/get_turnaround