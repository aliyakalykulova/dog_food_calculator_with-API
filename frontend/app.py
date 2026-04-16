import requests
import streamlit as st
from choose_dog_characteristics import choose_dog_characteristics

API_URL = "http://localhost:8000"  # потом поменяем при деплое

st.set_page_config(page_title="Рекомендации по питанию собак", layout="centered")
st.header("Рекомендации по питанию собак")

st.sidebar.title("🐶 Smart Dog Diet Advisor")
st.sidebar.write("Select breed + disorder → get personalized food suggestions")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/616/616408.png", width=80)   
  
# ---- Ввод характеристик собаки (choose_dog_characteristics.py)
 weight, age, age_metric, gender,  repro_status, berem_time, lact_time, num_puppy,  activity_for_adult, activity_for_senior, breed, disease,= choose_dog_characteristics(disease_df)

breed_size, avg_wight = size_category(disease_df[disease_df["name_breed"] == breed])  # --- Присвоение категории размера породы
age_type_categ = age_type_category(breed_size, age ,age_metric)     # --- Присвоение возрастной категории

if st.button("Составить рекомендации"):
    response = requests.post(
        f"{API_URL}/recommend",
        json={
			"weight": weight,
            "age": age,
            "age_metric": age_metric,
            "gender": gender,
            "reproductive_status": repro_status,
			"berem_time":berem_time,
			"lact_time":lact_time,
			"num_puppy":num_puppy,
			"activity_for_adult": activity_for_adult,
			"activity_for_senior": activity_for_senior,
			"breed": breed,
			"disease":disease,

            "size": breed_size,
            "avg_weight": avg_wight,
            "age_category": age_type_categ
        }
    )
    recomendations = response.json()

	
    # ---- Расчёт суточной потребности в калориях по формулам FEDIAF (norm_kcal_nutr.py)
	kcal=recomendations["kcal"]
    metobolic_energy = int(round(st.number_input("Киллокаллории в день", min_value=0.0, step=0.1,  value=round(kcal,1) ),1))

	
	# ---- Интерфейс для редактирования списка ингредиентов пользователем (ingredients_choose.py)
    ingredient_names = ingredients_choose(recomendations["ingredient_rec"])

    # ---- Интерфейс для редактирования пределов (min, max) содержания ингредиентов и нутриентов в корме (parametrs_for_linear_programming.py)
    ingr_ranges= ingredients_limits(ingredient_names)
    nutr_ranges = nutrients_limits(recomendations[nutrient_preds])
			 
	# ---- Выбор нутриентов для максимизации в корме (параметры линейного программирования) (parametrs_for_linear_programming.py) 
    maximaze_nutrs = maximize_function(recomendations["maximize_func"])


    if st.button("🔍 Рассчитать оптимальный состав"):
		response = requests.post(
        f"{API_URL}/calc_recipe",
        json={
			"ingredient_names": ingredient_names,
            "ingr_ranges": ingr_ranges,
            "nutr_ranges": nutr_ranges,
            "maximaze_nutrs": maximaze_nutrs
           }
         )
		recipe = response.json()
		
        show_recipe(recipe)

		 




import pandas as pd
from scipy.optimize import linprog  
import numpy as np

from functions.ingredients_choose import ingredients_choose  

from functions.parametrs_for_linear_programming import maximize_function
from functions.parametrs_for_linear_programming import ingredients_limits 
from functions.parametrs_for_linear_programming import nutrients_limits 
from functions.parametrs_for_linear_programming import lin_prog_parametrs

from functions.calc_recipe_method_2 import calc_recipe
from functions.show_results import show_resuts_success



	  # ---- При изменении данных о собаке (порода, заболевание) сбрасываются текущие рекомендации корма 
      if user_breed != st.session_state.user_breed or selected_disease!= st.session_state.disorder:
         st.session_state.user_breed = user_breed
         st.session_state.disorder = selected_disease
         st.session_state.show_result_1 = False
         st.session_state.show_result_2 = False
            
      # ---- Кнопка расчёта рекомендаций корма (калории, ингредиенты, нутриенты)
      if st.button("Составить рекомендации"):
         st.session_state.show_result_1 = True
	 
      if st.session_state.show_result_1:

		 # --- При изменении значения калорий сбрасывается рассчитанная рецептура корма	
         if st.session_state.kkal_sel!=metobolic_energy:
            st.session_state.kkal_sel=metobolic_energy
            st.session_state.show_result_1 = True
            st.session_state.show_result_2 = False

         
				
			   # --- При изменении пределов содержания ингредиентов и нутриентов сбрасывается рассчитанная рецептура корма
               if ingr_ranges != st.session_state.prev_ingr_ranges:
                  st.session_state.show_result_2 = False
                  st.session_state.prev_ingr_ranges = ingr_ranges.copy()
               if nutr_ranges != st.session_state.prev_nutr_ranges:
                  st.session_state.show_result_2 = False
                  st.session_state.prev_nutr_ranges = nutr_ranges.copy()
	  
			   # ---- Проверка соотношения ингредиентов и пропорциональная корректировка минимальных и максимальных пределов при нарушении условий
			   # ---- Проверка условия: сумма минимальных долей ингредиентов < 100, сумма максимальных долей > 100
               lowest=sum([low for (low, high) in ingr_ranges])
               highest=sum([high for (low, high) in ingr_ranges])
               ingr_ranges_2=ingr_ranges
               if lowest>100:
                  st.write("Минимальные доли ингредиентов превышают 100%. Значения были пропорционально уменьшены.")
                  factor=99/lowest
                  ingr_ranges_2=[(low*factor, high) for (low, high) in ingr_ranges]
               elif highest<100:
                  st.write("Максимальные доли ингредиентов меньше 100%. Значения были пропорционально увеличены.")
                  factor=101/highest
                  ingr_ranges_2=[(low, high*factor) for (low, high) in ingr_ranges]
				
			   # --- Подготовка параметров на основе заданных условий для расчёта рецептуры методом линейного программирования (parameters_for_linear_programming.py) 	   
               A, b, A_eq, b_eq,selected_maximize,f,bounds = lin_prog_parametrs(food,ingredient_names,nutr_ranges,ingr_ranges_2,maximaze_nutrs,nutrients_transl)
             
			   # --- Кнопка расчёта рецептуры	
               if st.button("🔍 Рассчитать оптимальный состав"):
                  st.session_state.show_result_2 = True

			
               if st.session_state.show_result_2:
				  # --- Расчёт рецептуры методом линейного программирования
                  res = linprog(f, A_ub=A, b_ub=b, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method="highs")

				  # --- Если решение найдено методом линейного программирования  
                  if res.success:
                     st.success("✅ Решение найдено!")
					  
					 # ---- Приведение результатов к удобному формату отображения (общее содержание нутриентов и соотношение ингредиентов)
                     nutrients_combo = {nutr: int(round(sum(res.x[i] * food[name][nutr]/100 for i, name in enumerate(ingredient_names)) * 100, 0))
                                       for nutr in main_nutrs}
                     ingredients_combo={name: int(round(val * 100, 0)) for name, val in zip(ingredient_names,res.x)}
                     best_recipe= (ingredients_combo,nutrients_combo)

					 # ---- Отображение результатов (show_results.py)
                     show_resuts_success(best_recipe,food,nutrients_transl,metobolic_energy, age_type_categ,
                                        ingredient_names, ingr_ranges,nutr_ranges)                         
                  else:
					 # ---- Если решение не найдено, используется комбинаторный метод
					 # ---- Расчёт рецептуры комбинаторным методом с выбором варианта с минимальным отклонением от нутриентных лимитов (calc_recipe_method_2.py)	 
                     best_recipe=calc_recipe(ingr_ranges_2,nutr_ranges,ingredient_names,food)
                     if best_recipe:
                        st.success("⚙️ Найден состав перебором:")
					    # ---- Отображение результатов (show_results.py)
                        show_resuts_success(best_recipe, food, nutrients_transl, metobolic_energy, age_type_categ,
                                            ingredient_names, ingr_ranges,nutr_ranges)
                     else:
                        st.error("🚫 Измените соотношение ингредиентов и/или нутриентов")
         else:
            st.info("👈 Пожалуйста, выберите хотя бы один ингредиент.")
