import streamlit as st

# ---- Ввод характеристик собаки пользователем: возраст, вес, пол, репродуктивный статус, уровень активности, порода, заболевание

metrics_age_types=["в годах","в месецах"]
gender_types=["Самец", "Самка"]
rep_status_types=["Нет", "Щенность (беременность)", "Период лактации"]
berem_time_types=["первые 4 недедели беременности","последние 5 недель беременности"]
lact_time_types=["1 неделя","2 неделя","3 неделя","4 неделя"]
age_category_types=["puppy","adult","senior"]
size_types=["small",  "medium",  "large"]
activity_for_adult = ["Пассивный (гуляеет на поводке менее 1ч/день)", "Средний1 (1-3ч/день, низкая активность)",
                        "Средний2 (1-3ч/день, высокая активность)", "Активный (3-6ч/день, рабочие собаки, например, овчарки)",
                        "Высокая активность в экстремальных условиях (гонки на собачьих упряжках со скоростью 168 км/день в условиях сильного холода)",
                        "Взрослые, склонные к ожирению"]
activity_for_senior = ["Пассивный", "Средний", "Активный"]

standard_care_map = {
    "puppy": "Уход за щенками",
    "adult": "Уход за взрослыми",
    "senior": "Уход за пожилыми"
}

# ---- Интерфейс выбора характеристик собаки
def choose_dog_characteristics_base(breed_list):

	weight,age,age_metric,gender,repro_status,berem_time,lact_time,num_puppy,breed= ( "", "", "", "", "", "", "", "", "")

   col1, col0 ,col2, col3 = st.columns([3,1, 3, 2]) 
   with col1:
      weight = st.number_input("Вес собаки (в кг)", min_value=0.0, step=0.1)   # --- Ввод веса собаки
   with col2:
     age = st.number_input("Возраст собаки", min_value=0, step=1)             # --- Ввод возраста собаки
   with col3:
      age_metric=st.selectbox("Измерение возроста", metrics_age_types)         # --- Выбор единицы измерения возраста
   gender = st.selectbox("Пол собаки", gender_types)                           # --- Выбор пола собаки

   # --- Если пол собаки "самка", отображается инструмент выбора репродуктивного статуса
   if gender == gender_types[1]:
      col1, col2 = st.columns([1, 20])  
      with col2:
         repro_status = st.selectbox( "Репродуктивный статус", rep_status_types)  # --- Ввод репродуктивного статуса собаки
			 
      # --- Если репродуктивный статус "беременность", отображается инструмент ввода срока беременности
      if repro_status==rep_status_types[1]:
            col1, col2 = st.columns([3, 20])  
            with col2:            
              berem_time=st.selectbox("Срок беременности", berem_time_types)  # --- Ввод срока беременности
            				  
      # --- Если репродуктивный статус "период лактации", отображается инструмент ввода характеристик лактации
      elif repro_status==rep_status_types[2] :
            col1, col2 = st.columns([3, 20])  
            with col2:  
               lact_time=st.selectbox("Лактационный период", lact_time_types)       # --- Ввод периода лактации 
               num_puppy=st.number_input("Количесвто щенков", min_value=0, step=1)    # --- Ввод количества щенков
				
	  # --- Если репродуктивный статус отсутствует		
	  else:
		  berem_time=""
		  lact_time=""
		  num_puppy=0

   # --- Если пол собаки "самец", сброс репродуктивного статуса
   else:
      repro_status =""
	  berem_time=""
	  lact_time=""
	  num_puppy=0
	   
   # ---- Выбор породы
   breed = st.selectbox("Порода собаки:", breed_list)   # --- Ввод породы собаки
    
   return	weight,age,age_metric,gender,repro_status,berem_time,lact_time,num_puppy,breed


def choose_dog_characteristics_additional(age_type_categ, diseases):

   activity_for_adult, activity_for_senior, disorder=("","","")

   # --- Выбор уровня активности для возрастной категории "взрослый"
   if age_type_categ==age_category_types[1]:
      activity_for_adult = st.selectbox("Уровень активности", activity_for_adult)
      activity_for_senior=""

   # ---Выбор уровня активности для возрастной категории "пожилой"
   elif age_type_categ==age_category_types[2]:
      activity_for_senior  = st.selectbox("Уровень активности",activity_for_senior)
      activity_for_adult=""
   else:
      activity_for_adult=""
      activity_for_senior=""

   # ---- Выбор из списка возможных заболеваний в зависимости от породы
   disorder = st.selectbox("Заболевание:", diseases)

   return activity_for_adult, activity_for_senior, disorder
