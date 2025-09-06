import streamlit as st
import pandas as pd
import requests
import re
import textwrap
import io
import os
from dotenv import load_dotenv

# 🔑 Load API key from .env file
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/completions"

st.set_page_config(page_title="AI Data Analyst", layout="wide")

st.title("🤖 AI Data Analyst")
st.write("Upload a CSV and ask questions in natural language!")
st.markdown(
        """
        <style>
        .fixed-bottom {
        position: fixed;
        bottom: 10px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 12px;
        color: black; /* Changed to black for contrast on light body */
        background-color: rgb(240, 242, 246); /* Match body background */
        padding: 5px 10px;
        border-radius: 5px;
        z-index: 1000;
    }
    </style>
    <div class="fixed-bottom">made with ❤️ from Sohan </div>
    """, 
    unsafe_allow_html=True
    )

# Step 1: Upload CSV
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.write("✅ Data loaded successfully!")
    st.dataframe(df.head())

    # Step 2: Take natural language query
    user_query = st.text_input("Ask a question about your data:")

    if st.button("Analyze") and user_query:
        # Step 3: Convert NL → Pandas + SQL code using LLM
        prompt = f"""
        You are a data analyst. The user uploaded a dataframe called df with these columns:
        {list(df.columns)}.

        Task:
        1. Generate valid Python Pandas code to answer the question. The code must assign the final output to a variable called 'result'.
        2. Generate an equivalent SQL query. Assign it to a variable called 'sql_query'.

        Return two separate code blocks:
        ```python
        # pandas code here
        ```
        ```sql
        -- sql code here
        ```

        User question: {user_query}
        """

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "openai/gpt-3.5-turbo-instruct",  # you can swap with other models
            "prompt": prompt,
            "max_tokens": 1500
        }

        response = requests.post(API_URL, headers=headers, json=payload)

        if response.status_code == 200:
            data = response.json()
            raw_text = data["choices"][0]["text"].strip()

            # Extract Python + SQL code blocks
            python_code_match = re.search(r"```python(.*?)```", raw_text, re.S)
            sql_code_match = re.search(r"```sql(.*?)```", raw_text, re.S)

            python_code = python_code_match.group(1).strip() if python_code_match else None
            sql_query = sql_code_match.group(1).strip() if sql_code_match else None

            if python_code:
                # Dedent & clean Python code to avoid indent errors
                python_code = textwrap.dedent(python_code).strip()

                st.subheader("🐍 Generated Pandas Code")
                st.code(python_code, language="python")

                try:
                    # Step 4: Execute Pandas code safely
                    local_vars = {"df": df}
                    exec(python_code, {}, local_vars)
                    result = local_vars.get("result", None)

                    if result is not None:
                        st.subheader("🔹 Pandas Result")
                        if isinstance(result, (pd.DataFrame, pd.Series)):
                            st.dataframe(result)
                        else:
                            st.write(result)
                    else:
                        st.write("⚠️ No result returned.")
                except Exception as e:
                    st.error(f"Error executing code: {e}")

            if sql_query:
                st.subheader("📝 Equivalent SQL Query")
                st.code(sql_query, language="sql")

        else:

            st.error(f"API request failed: {response.text}")
