
# ---- Определение категории размера породы на основе стандартного веса собаки
def size_category(df):
   w = (df["min_weight"].iloc[0] + df["max_weight"].iloc[0]) / 2  
   if w <= 10:
      return size_types[0],w    # --- Категория "small"
   elif w <= 25:
      return size_types[1],w    # --- Категория "medium"
   else :
      return size_types[2],w    # --- Категория "large"

# ---- Определение возрастной категории на основе возраста и категории размера породы
def age_type_category(size_categ, age ,age_metric):
   # --- Перевод единицы измерения возраста из лет в месяцы
   if age_metric==metrics_age_types[0]:     
      age=age*12
     
   # --- Для мелких пород собак  
   if size_categ==size_types[0]:
      if age>=1*12 and age<=8*12:       # --- Категория "щенок"
         return age_category_types[1]
      elif age<1*12:                    # --- Категория "взрослый"
         return age_category_types[0]
      elif age>8*12:                    # --- Категория "пожилой"
         return age_category_types[2]
        
   # --- Для средних пород собак       
   elif size_categ==size_types[2]:
      if age>=15 and age<=7*12  :       # --- Категория "щенок"
         return age_category_types[1]   
      elif age<15:                      # --- Категория "взрослый" 
         return age_category_types[0]
      elif age>7*12:                    # --- Категория "пожилой"
         return age_category_types[2]
        
   # --- Для крупных пород собак             
   else:
      if age<=6*12 and age>=24:         # --- Категория "щенок"
         return age_category_types[1]
      elif age<24:                      # --- Категория "взрослый" 
         return age_category_types[0]
      elif age>6*12:                    # --- Категория "пожилой"
         return age_category_types[2]
