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

# सेशन स्टेट सुरू करणे (पेज नेव्हिगेशनसाठी)
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = None
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False

# --- स्वतंत्र प्रोफाईल व्ह्यू (जेव्हा नावावर क्लिक होईल) ---
if st.session_state.selected_customer is not None:
    cust_mobile = st.session_state.selected_customer
    cust_data = df[df["मोबाईल"].astype(str) == str(cust_mobile)].iloc[0]
    
    st.button("⬅️ मुख्य यादीकडे परत जा", on_click=lambda: st.session_state.update({"selected_customer": None, "edit_mode": False}))
    
    st.title(f"👤 {cust_data['नाव']} यांची प्रोफाईल")
    
    # फोटो दाखवणे (१:१ क्रॉप केलेला फोटो)
    if pd.notna(cust_data["फोटो_पाथ"]) and os.path.exists(cust_data["फोटो_पाथ"]):
        st.image(cust_data["फोटो_पाथ"], width=200, caption=cust_data['नाव'])
    else:
        st.warning("या प्रोफाईलला फोटो अपलोड केलेला नाही.")
        
    if not st.session_state.edit_mode:
        # माहिती फक्त दाखवणे (View Mode)
        st.write(f"**📍 पत्ता:** {cust_data['पत्ता']}")
        st.write(f"**📞 मोबाईल:** {cust_data['मोबाईल']}")
        st.write(f"**🎂 जन्मतारीख:** {cust_data['जन्मतारीख']} (वय: {cust_data['वय']} वर्षे)")
        st.write(f"**💑 लग्नाची तारीख:** {cust_data['लग्नाची_तारीख']}")
        st.write(f"**📊 कॅटेगरी व स्टेटस:** {cust_data['कॅटेगरी']}")
        st.write(f"**🔄 एकूण थेरपी भेटी:** {cust_data['एकूण_भेटी']}")
        st.write(f"**🤝 संदर्भ (Referred By):** {cust_data['संदर्भ_दिलेला_व्यक्ती']}")
        
        st.button("📝 माहिती संपादन करा (Edit Profile)", on_click=lambda: st.session_state.update({"edit_mode": True}))
    else:
        # माहिती बदलणे (Edit Mode)
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
            
            save_edit = st.form_submit_button("बदल जतन करा (Save)")
            
            if save_edit:
                # नवीन वयाची गणना
                new_age = today.year - new_dob.year - ((today.month, today.day) < (new_dob.month, new_dob.day))
                anniv_str = str(new_anniv) if new_has_anniv else "नाही"
                
                # डेटा अपडेट करणे
                df.loc[df["मोबाईल"].astype(str) == str(cust_mobile), ["नाव", "पत्ता", "जन्मतारीख", "लग्नाची_तारीख", "वय", "संदर्भ_दिलेला_व्यक्ती"]] = [
                    new_name, new_address, str(new_dob), anniv_str, new_age, new_ref
                ]
                save_data(df)
                st.success("माहिती यशस्वीरित्या सुधारली आहे!")
                st.session_state.edit_mode = False
                st.rerun()
else:
    # --- मुख्य स्क्रीन (डेटा एंट्री आणि यादी) ---
    st.title("🏥 ऑटोमॅटिक थेरपी बेड व्यवस्थापन अ‍ॅप")

    # --- विभाग १: रिमांडर्स ---
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

    # --- विभाग २: डेटा एंट्री फॉर्म ---
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
        uploaded_photo = st.file_uploader("फोटो (फक्त पहिल्या भेटीत अनिवार्य)", type=["jpg", "png", "jpeg"])

        submitted = st.form_submit_button("नोंदणी करा")

        if submitted:
            if not name or not address or not mobile:
                st.error("कृपया अनिवार्य माहिती भरा!")
            else:
                age = today.year - dob_input.year - ((today.month, today.day) < (dob_input.month, dob_input.day))
                existing_customer = df[df["मोबाईल"].astype(str) == str(mobile)]
                
                if not existing_customer.empty:
                    visits = existing_customer.iloc[0]["एकूण_भेटी"] + 1
                    photo_path = existing_customer.iloc[0]["फोटो_path"] if "फोटो_path" in existing_customer.columns else "नाही"
                    df.loc[df["मोबाईल"].astype(str) == str(mobile), ["एकूण_भेटी", "वय"]] = [visits, age]
                else:
                    visits = 1
                    photo_path = "नाही"
                    if uploaded_photo is not None:
                        # १:१ सेंटर क्रॉपिंग बॅकएंड लॉजिक
                        img = Image.open(uploaded_photo)
                        width, height = img.size
                        min_dim = min(width, height)
                        left = (width - min_dim) / 2
                        top = (height - min_dim) / 2
                        right = (width + min_dim) / 2
                        bottom = (height + min_dim) / 2
                        img_cropped = img.crop((left, top, right, bottom))
                        
                        photo_path = os.path.join(PHOTO_FOLDER, f"{mobile}.jpg")
                        img_cropped.save(photo_path)
                
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
                st.success(f"नोंद यशस्वी! भेट संख्या: {visits} ({customer_status})")
                st.clear_checkboxes() if hasattr(st, "clear_checkboxes") else st.rerun()

    st.markdown("---")

    # --- विभाग ३: ग्राहकांची परस्परसंवादी यादी ---
    st.subheader("📋 ग्राहकांची यादी (प्रोफाईल पाहण्यासाठी नावावर क्लिक करा)")
    if not df.empty:
        for index, row in df.iterrows():
            # प्रत्येक ग्राहकासाठी एक लिंक बटण तयार करणे
            if st.button(f"👤 {row['नाव']} | 📞 {row['मोबाईल']} | 🔄 भेटी: {row['एकूण_भेटी']}", key=f"cust_{row['मोबाईल']}"):
                st.session_state.selected_customer = row['मोबाईल']
                st.rerun()
    else:
        st.write("अजून कोणतीही नोंदणी नाही.")
