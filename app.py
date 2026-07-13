import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# डेटा आणि फोटो साठवण्यासाठी फोल्डर निश्चित करणे
DATA_FILE = "therapy_customers.csv"
PHOTO_FOLDER = "customer_photos"

if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)

# डेटा लोड करण्यासाठी फंक्शन
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "नाव", "पत्ता", "मोबाईल", "जन्मतारीख", "लग्नाची_तारीख", 
            "वय", "फोटो_पाथ", "संदर्भ_दिलेला_व्यक्ती", "कॅटेगरी", "एकूण_भेटी"
        ])

# डेटा सेव्ह करण्यासाठी फंक्शन
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()

st.title("🏥 ऑटोमॅटिक थेरपी बेड व्यवस्थापन अ‍ॅप")

# --- विभाग १: वाढदिवस आणि लग्नाचा वाढदिवस रिमाइंडर (आज आणि उद्या) ---
st.subheader("🔔 आगामी रिमाइंडर्स (आज आणि उद्या)")

today = datetime.now().date()
tomorrow = today + timedelta(days=1)

reminder_list = []
for index, row in df.iterrows():
    # वाढदिवस तपासणे
    if pd.notna(row["जन्मतारीख"]):
        dob = datetime.strptime(row["जन्मतारीख"], "%Y-%m-%d").date()
        if (dob.month == today.month and dob.day == today.day):
            reminder_list.append(f"🎉 **आज वाढदिवस आहे:** {row['नाव']} ({row['मोबाईल']})")
        elif (dob.month == tomorrow.month and dob.day == tomorrow.day):
            reminder_list.append(f"⏰ **उद्या वाढदिवस आहे:** {row['नाव']} ({row['मोबाईल']})")
    
    # लग्नाचा वाढदिवस तपासणे
    if pd.notna(row["लग्नाची_तारीख"]) and row["लग्नाची_तारीख"] != "नाही":
        anniv = datetime.strptime(row["लग्नाची_तारीख"], "%Y-%m-%d").date()
        if (anniv.month == today.month and anniv.day == today.day):
            reminder_list.append(f"💑 **आज लग्नाचा वाढदिवस आहे:** {row['नाव']} ({row['मोबाईल']})")
        elif (anniv.month == tomorrow.month and anniv.day == tomorrow.day):
            reminder_list.append(f"⏰ **उद्या लग्नाचा वाढदिवस आहे:** {row['नाव']} ({row['मोबाईल']})")

if reminder_list:
    for r in reminder_list:
        st.info(r)
else:
    st.write("आज किंवा उद्या कोणाचाही वाढदिवस किंवा लग्नाचा वाढदिवस नाही.")

st.markdown("---")

# --- विभाग २: ग्राहक डेटा एंट्री फॉर्म ---
st.subheader("📝 नवीन भेट नोंदवा")

with st.form("customer_form", clear_on_submit=True):
    name = st.text_input("ग्राहकाचे नाव *")
    address = st.text_input("पत्ता *")
    mobile = st.text_input("मोबाईल नंबर *")
    
    dob_input = st.date_input("जन्मतारीख *", min_value=datetime(1920, 1, 1), max_value=datetime.now())
    
    # लग्नाची तारीख Optional ठेवण्यासाठी चेकबॉक्स
    has_anniversary = st.checkbox("लग्नाची तारीख नोंदवायची आहे का?")
    anniversary_input = None
    if has_anniversary:
        anniversary_input = st.date_input("लग्नाची तारीख", min_value=datetime(1950, 1, 1), max_value=datetime.now())
        
    category_type = st.selectbox("कॅटेगरी", ["Male", "Female", "Couple", "Family"])
    referred_by = st.text_input("Refered By (कोणाचा संदर्भ आहे?)")
    
    # फोटो अपलोडर (फक्त पहिल्या भेटीत)
    uploaded_photo = st.file_uploader("ग्राहकाचा फोटो अपलोड करा (फक्त पहिल्या भेटीत अनिवार्य)", type=["jpg", "png", "jpeg"])

    submitted = st.form_submit_with_button("नोंदणी करा")

    if submitted:
        if not name or not address or not mobile:
            st.error("कृपया सर्व अनिवार्य (*) माहिती भरा!")
        else:
            # वय स्वयंचलित मोजणे
            age = today.year - dob_input.year - ((today.month, today.day) < (dob_input.month, dob_input.day))
            
            # आधीच्या भेटी तपासणे (मोबाईल नंबरवरून युनिक ओळख)
            existing_customer = df[df["मोबाईल"].astype(str) == str(mobile)]
            
            if not existing_customer.empty:
                # जुना ग्राहक असल्यास: भेटीची संख्या १ ने वाढवणे
                visits = existing_customer.iloc[0]["एकूण_भेटी"] + 1
                photo_path = existing_customer.iloc[0]["फोटो_पाथ"] # जुनाच फोटो वापरणे
                
                # जुना डेटा अपडेट करणे
                df.loc[df["मोबाईल"].astype(str) == str(mobile), "एकूण_भेटी"] = visits
                df.loc[df["मोबाईल"].astype(str) == str(mobile), "वय"] = age
            else:
                # नवीन ग्राहक असल्यास
                visits = 1
                photo_path = "नाही"
                
                # पहिल्या भेटीत फोटो अपलोड केला असल्यास सेव्ह करणे
                if uploaded_photo is not None:
                    photo_path = os.path.join(PHOTO_FOLDER, f"{mobile}.jpg")
                    with open(photo_path, "wb") as f:
                        f.write(uploaded_photo.getbuffer())
            
            # कस्टमर स्टेटस ऑटोमॅटिक ठरवणे (१ ते ५: New Customer, ५ पेक्षा जास्त: Regular)
            customer_status = "New Customer" if visits <= 5 else "Regular"
            anniversary_str = str(anniversary_input) if has_anniversary else "नाही"
            
            if existing_customer.empty:
                # नवीन ग्राहकाची रो तयार करून जोडणे
                new_row = {
                    "नाव": name, "पत्ता": address, "मोबाईल": mobile, 
                    "जन्मतारीख": str(dob_input), "लग्नाची_तारीख": anniversary_str, 
                    "वय": age, "फोटो_पाथ": photo_path, "संदर्भ_दिलेला_व्यक्ती": referred_by, 
                    "कॅटेगरी": f"{category_type} ({customer_status})", "एकूण_भेटी": visits
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            
            save_data(df)
            st.success(f"नोंद यशस्वी! {name} यांची भेट संख्या: {visits} ({customer_status}) | वय: {age}")

st.markdown("---")

# --- विभाग ३: डेटा डिस्प्ले (ग्राहकांची यादी) ---
st.subheader("📋 आजवर नोंदणी झालेले ग्राहक")
if not df.empty:
    st.dataframe(df[["नाव", "मोबाईल", "वय", "कॅटेगरी", "एकूण_भेटी", "पत्ता"]])
else:
    st.write("अजून कोणतीही नोंदणी झालेली नाही.")
