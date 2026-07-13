import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from PIL import Image

# डेटा आणि फोटो साठवण्यासाठी फोल्डर निश्चित करणे
DATA_FILE = "therapy_customers.csv"
PHOTO_FOLDER = "customer_photos"

if not os.path.exists(PHOTO_FOLDER):
    os.makedirs(PHOTO_FOLDER)

# डेटा लोड फंक्शन
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "नाव", "पत्ता", "मोबाईल", "जन्मतारीख", "लग्नाची_तारीख", 
            "वय", "फोटो_पाथ", "संदर्भ_दिलेला_व्यक्ती", "कॅटेगरी", "एकूण_भेटी"
        ])

# डेटा सेव्ह फंक्शन
def save_data(df):
    df.to_csv(DATA_FILE, index=False)

df = load_data()
today = datetime.now().date()

# सेशन State व्यवस्थापन
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# फोटो मॅन्युअल क्रॉप करण्यासाठीचे फंक्शन
def crop_image_manually(uploaded_file, key_prefix):
    st.write("📸 **फोटो संपादन (Manual Crop Option):**")
    img = Image.open(uploaded_file)
    w, h = img.size
    
    # मॅन्युअल क्रॉपिंग स्लाईडर्स
    crop_w = st.slider("रुंदी कमी-जास्त करा (Width)", 10, w, w, key=f"{key_prefix}_w")
    crop_h = st.slider("उंची कमी-जास्त करा (Height)", 10, h, min(w, h), key=f"{key_prefix}_h")
    
    left = (w - crop_w) / 2
    top = (h - crop_h) / 2
    right = left + min(crop_w, crop_h)
    bottom = top + min(crop_w, crop_h)
    
    img_cropped = img.crop((left, top, right, bottom))
    st.image(img_cropped, caption="अंतिम क्रॉप झालेला फोटो (१:१ प्रमाणात)", width=150)
    return img_cropped

# --- स्वतंत्र प्रोफाईल व्ह्यू ---
if st.session_state.selected_customer is not None:
    cust_mobile = st.session_state.selected_customer
    cust_data = df[df["मोबाईल"].astype(str) == str(cust_mobile)].iloc[0]
    
    st.button("⬅️ मुख्य यादीकडे परत जा", on_click=lambda: st.session_state.update({"selected_customer": None, "edit_mode": False}))
    
    st.title(f"👤 {cust_data['नाव']} यांची प्रोफाईल")
    
    if pd.notna(cust_data["फोटो_पाथ"]) and os.path.exists(cust_data["फोटो_पाथ"]):
        st.image(cust_data["फोटो_path"], width=200, caption=cust_data['नाव'])
    else:
        st.warning("या प्रोफाईलला फोटो अपलोड केलेला नाही.")
        
    if not st.session_state.edit_mode:
        st.write(f"**📍 पत्ता:** {cust_data['पत्ता']}")
        st.write(f"**📞 मोबाईल:** {cust_data['मोबाईल']}")
        st.write(f"**🎂 जन्मतारीख:** {cust_data['जन्मतारीख']} (वय: {cust_data['वय']} वर्षे)")
        st.write(f"**💑 लग्नाची तारीख:** {cust_data['लग्नाची_तारीख']}")
        st.write(f"**📊 कॅटेगरी व स्टेटस:** {cust_data['कॅटेगरी']}")
        st.write(f"**🔄 एकूण थेरपी भेटी:** {cust_data['एकूण_भेटी']}")
        st.write(f"**🤝 संदर्भ (Referred By):** {cust_data['संदर्भ_दिलेला_व्यक्ती']}")
        
        st.button("📝 माहिती संपादन करा (Edit Profile)", on_click=lambda: st.session_state.update({"edit_mode": True}))
    else:
        st.subheader("⚙️ माहिती सुधारा")
        with st.form("edit_form"):
            new_name = st.text_input("नाव", value=cust_data['नाव'])
            new_address = st.text_input("पत्ता", value=cust_data['पत्ता'])
            
            dob_dt = datetime.strptime(cust_data['जन्मतारीख'], "%Y-%m-%d").date()
            new_dob = st.date_input("जन्मतारीख", value=dob_dt)
            
            has_anniv = cust_data['लग्नाची_तारीख'] != "नाही"
            anniv_val = datetime.strptime(cust_data['लग्नाची_तारीख'], "%Y-%m-%d").date() if has_anniv else today
            new_has_anniv = st.checkbox("लग्नाची तारीख आहे का?", value=has_anniv)
            new_anniv = st.date_input("लग्नाची तारीख", value=anniv_val) if new_has_anniv else "नाही"
            
            new_ref = st.text_input("Refered By", value=cust_data['संदर्भ_दिलेला_व्यक्ती'])
            new_photo = st.file_uploader("नवीन फोटो अपडेट करा (ऐच्छिक)", type=["jpg", "png", "jpeg"])
            
            cropped_img_edit = None
            if new_photo is not None:
                cropped_img_edit = crop_image_manually(new_photo, "edit")
                
            save_edit = st.form_submit_button("बदल जतन करा (Save Changes)")
            
            if save_edit:
                new_age = today.year - new_dob.year - ((today.month, today.day) < (new_dob.month, new_dob.day))
                anniv_str = str(new_anniv) if new_has_anniv else "नाही"
                photo_path = cust_data["फोटो_पाथ"]
                
                if cropped_img_edit is not None:
                    photo_path = os.path.join(PHOTO_FOLDER, f"{cust_mobile}.jpg")
                    cropped_img_edit.save(photo_path)
                
                df.loc[df["मोबाईल"].astype(str) == str(cust_mobile), ["नाव", "पत्ता", "जन्मतारीख", "लग्नाची_तारीख", "वय", "संदर्भ_दिलेला_व्यक्ती", "फोटो_पाथ"]] = [
                    new_name, new_address, str(new_dob), anniv_str, new_age, new_ref, photo_path
                ]
                save_data(df)
                st.success("माहिती यशस्वीरित्या सुधारली आहे!")
                st.session_state.edit_mode = False
                st.rerun()
else:
    # --- मुख्य स्क्रीन ---
    st.title("🏥 ऑटोमॅटिक थेरपी बेड व्यवस्थापन अ‍ॅप")

    # --- विभाग १: रिमांडर्स (पूर्णपणे दुरुस्त केलेला भाग) ---
    st.subheader("🔔 आगामी रिमाइंडर्स (आज आणि उद्या)")
    tomorrow = today + timedelta(days=1)
    reminder_list = []
    
    for index, row in df.iterrows():
        if pd.notna(row["जन्मतारीख"]):
            dob = datetime.strptime(row["जन्मतारीख"], "%Y-%m-%d").date()
            if (dob.month == today.month and dob.day == today.day):
                reminder_list.append(f"🎉 **आज वाढदिवस:** {row['नाव']}")
            elif (dob.month == tomorrow.month and dob.day == tomorrow.day):
                reminder_list.append(f"⏰ **उद्या वाढदिवस:** {row['नाव']}")
        
        # दोन्ही बाजूचे स्पेलिंग अचूक मराठीत दुरुस्त केले आहे
        if pd.notna(row["लग्नाची_तारीख"]) and row["लग्नाची_तारीख"] != "नाही":
            anniv = datetime.strptime(row["लग्नाची_तारीख"], "%Y-%m-%d").date()
            if (anniv.month == today.month and anniv.day == today.day):
                reminder_list.append(f"💑 **आज लग्नाचा वाढदिवस:** {row['नाव']}")
            elif (anniv.month == tomorrow.month and anniv.day == tomorrow.day):
                reminder_list.append(f"⏰ **उद्या लग्नाचा वाढदिवस:** {row['नाव']}")

    if reminder_list:
        for r in reminder_list: st.info(r)
    else: st.write("आज किंवा उद्या कोणतेही रिमाइंडर्स नाहीत.")

    st.markdown("---")

    # --- विभाग २: ग्राहक डेटा एंट्री फॉर्म ---
    st.subheader("📝 नवीन भेट नोंदवा")
    with st.form("customer_form", clear_on_submit=True):
        name = st.text_input("ग्राहकाचे नाव *")
        address = st.text_input("पत्ता *")
        mobile = st.text_input("मोबाईल नंबर *")
        dob_input = st.date_input("जन्मतारीख *", min_value=datetime(1920, 1, 1), max_value=datetime.now())
        
        has_anniversary = st.checkbox("लग्नाची तारीख नोंदवायची आहे?")
        anniversary_input = st.date_input("लग्नाची तारीख", max_value=datetime.now()) if has_anniversary else None
            
        category_type = st.selectbox("कॅटेगरी", ["Male", "Female", "Couple", "Family"])
        referred_by = st.text_input("Refered By")
        uploaded_photo = st.file_uploader("फोटो अपलोड करा *", type=["jpg", "png", "jpeg"])
        
        cropped_img_new = None
        if uploaded_photo is not None:
            cropped_img_new = crop_image_manually(uploaded_photo, "new")

        submitted = st.form_submit_button("नोंदणी करा")

        if submitted:
            if not name or not address or not mobile:
                st.error("कृपया अनिवार्य माहिती भरा!")
            else:
                age = today.year - dob_input.year - ((today.month, today.day) < (dob_input.month, dob_input.day))
                existing_customer = df[df["मोबाईल"].astype(str) == str(mobile)]
                
                if not existing_customer.empty:
                    visits = existing_customer.iloc[0]["एकूण_भेटी"] + 1
                    photo_path = existing_customer.iloc[0]["फोटो_पाथ"]
                    df.loc[df["मोबाईल"].astype(str) == str(mobile), ["एकूण_भेटी", "वय"]] = [visits, age]
                else:
                    visits = 1
                    photo_path = "नाही"
                    if cropped_img_new is not None:
                        photo_path = os.path.join(PHOTO_FOLDER, f"{mobile}.jpg")
                        cropped_img_new.save(photo_path)
                
                customer_status = "New Customer" if visits <= 5 else "Regular"
                anniversary_str = str(anniversary_input) if has_anniversary else "नाही"
                
                if existing_customer.empty:
                    new_row = {
                        "नाव": name, "पत्ता": address, "मोबाईल": mobile, 
                        "जन्मतारीख": str(dob_input), "लग्नाची_तारीख": anniversary_str, 
                        "वय": age, "फोटो_पाथ": photo_path, "संदर्भ_दिलेला_व्यक्ती": referred_by, 
                        "कॅटेगरी": f"{category_type} ({customer_status})", "एकूण_भेटी": visits
                    }
                    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                
                save_data(df)
                st.success(f"नोंद यशस्वी! भेट संख्या: {visits}")
                st.rerun()

    st.markdown("---")

    # --- विभाग ३: ग्राहकांची फक्त नावासहित लिस्ट व्ह्यू यादी ---
    st.subheader("📋 ग्राहकांची यादी")
    if not df.empty:
        for index, row in df.iterrows():
            if st.button(f"👤 {row['नाव']}", key=f"list_{row['मोबाईल']}", use_container_width=True):
                st.session_state.selected_customer = row['मोबाईल']
                st.rerun()
    else:
        st.write("अहून कोणतीही नोंदणी नाही.")
