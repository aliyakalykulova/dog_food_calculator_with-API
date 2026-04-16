from fastapi import FastAPI
from pydantic import BaseModel

import pandas as pd
from scipy.optimize import linprog  
import numpy as np

from functions.connect_database import  load_data

from functions.train_models import build_text_pipeline
from functions.train_models import build_categorical_encoder
from functions.train_models import combine_features
from functions.train_models import train_ingredient_models
from functions.train_models import train_nutrient_models
from functions.train_models import  apply_category_masks

from category_dog_def import size_category
from category_dog_def import age_type_category

from functions.norm_kcal_nutr import kcal_calculate

from functions.recommend_ingredients_nutrients import ingredient_recommendation
from functions.recommend_ingredients_nutrients import nutrients_recommendation
from functions.ingredients_choose import ingredients_choose  

from functions.parametrs_for_linear_programming import maximize_function
from functions.parametrs_for_linear_programming import ingredients_limits 
from functions.parametrs_for_linear_programming import nutrients_limits 

main_nutrs=['moisture_per', 'protein_per', 'carbohydrate_per', 'fats_per']

standard_care_map = {
    "puppy": "Уход за щенками",
    "adult": "Уход за взрослыми",
    "senior": "Уход за пожилыми"
}

# ---- Загрузка данных из базы данных (connect_database.py)
food_df, disease_df, df_standart, ingredirents_df,nutrients_transl= load_data()

# ---- Обучение модели рекомендации ингредиентов (train_models.py)
vectorizer, svd, X_text_reduced = build_text_pipeline(food_df["description"], n_components=100)
encoder, X_categorical = build_categorical_encoder(food_df)
X_categorical=apply_category_masks(X_categorical,encoder)
X_combined = combine_features(X_text_reduced, X_categorical)
ingredient_models, frequent_ingredients = train_ingredient_models(food_df, X_combined)

# ---- Обучение модели расчёта количества нутриентов (только влажные корма) (train_models.py)
vectorizer_wet, svd_wet, X_text_reduced_wet = build_text_pipeline(food_df[food_df["food_form"]=="wet food"]["description"], n_components=100)
encoder_wet, X_categorical_wet = build_categorical_encoder(food_df[food_df["food_form"]=="wet food"])
X_categorical_wet=apply_category_masks(X_categorical_wet,encoder_wet)
X_combined_wet = combine_features(X_text_reduced_wet, X_categorical_wet)
ridge_models, scalers = train_nutrient_models(food_df[food_df["food_form"]=="wet food"], X_combined_wet)



app = FastAPI()

# ---- модель запроса
class CategorDefRequest(BaseModel):
    breed: str
    age: int
    age_metric: str

# ---- список пород (исправили на GET)
@app.get("/breed_list")
async def get_breed_list():
    breed_list = sorted(disease_df["name_breed"].unique())
    return {"breed_list": breed_list}

# ---- расчет характеристик
@app.post("/categor_def")
async def categor_def(request: CategorDefRequest):
    breed = request.breed
    age = request.age
    age_metric = request.age_metric

    breed_size, avg_weight = size_category(
        disease_df[disease_df["name_breed"] == breed]
    )

    age_category = age_type_category(breed_size, age, age_metric)
    info = disease_df[disease_df["name_breed"] == breed]
    st_c = standard_care_map.get(age_category)
    diseases = [
        dis for dis in info["name_disease"].unique().tolist()
        if dis not in standard_care_map.values() or dis == st_c
    ]

    return {
        "age_category": age_category,
        "breed_size": breed_size,
        "avg_weight": avg_weight,
        "disease": diseases
    }


# ---- модель запроса
class RecomendRequest(BaseModel):
    weight :float
    age :int
    age_metric : str
	gender: str

@app.post("/recomendations")
async def categor_def(request: RecomendRequest):

    weight = request.weight
    age = request.age
    age_metric = request.age_metric
	gender=request.gender
    repro_status=request.repro_status
	berem_time=request.berem_time
	L_time=request.lact_time
	num_pup=request.num_puppy
	activity_for_adult=request.activity_for_adult
	activity_for_senior=request.activity_for_senior
	breed=request.breed
	disease=request.disease
    breed_size=request.breed_size
    avg_weight=request.avg_weight
    age_category=request.age_category

	info = disease_df[disease_df["name_breed"] == breed]
    match = info.loc[info["name_disease"] == disease, "name_disorder"]
    disorder_type = match.iloc[0] if not match.empty else disease

    kcal=kcal_calculate(age_type_categ, avg_wight,weight,age,age_metric, repro_status,berem_time,num_pup,L_time,activity_for_adult,activity_for_senior,breed)

    # --- Вычисление рекомендаций ингредиентов и количества нутриентов с помощью обученных моделей (recommend_ingredients_nutrients.py)
    ingredients_finish,keywords=ingredient_recommendation(ingredient_models,breed_size, age_type_categ,disorder_type, selected_disease,vectorizer,svd,encoder, df_standart)
    nutrient_preds = nutrients_recommendation(vectorizer_wet,keywords,svd_wet,encoder_wet, breed_size, age_type_categ, ridge_models,scalers )

    # ---- Выбор нутриентов для максимизации в корме (параметры линейного программирования) (parametrs_for_linear_programming.py) 
    maximaze_nutrs = maximize_function(food_df, nutrient_preds)
			 
            if ingredient_names:
			   # ---- Установка пределов (min, max) содержания ингредиентов и нутриентов в корме (parametrs_for_linear_programming.py)
               ingr_ranges= ingredients_limits(ingredirents_df, ingredient_names)
               nutr_ranges = nutrients_limits(nutrient_preds)
				
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
				


    return {
        "kcal": kcal,
        "ingredient_rec": ingredient_rec,
        "nutrient_preds": nutrient_preds,
        "maximize_func": maximize_func
    }



   





from functions.parametrs_for_linear_programming import lin_prog_parametrs

from functions.calc_recipe_method_2 import calc_recipe
from functions.show_results import show_resuts_success





		
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
