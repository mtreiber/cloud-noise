import streamlit as st
import pdal
import json
import os
import tempfile
import zipfile
import io

st.set_page_config(page_title="LAS/LAZ Denoiser", layout="centered")

st.title("🌲 Point Cloud Noise Filter (PDAL)")

# --- Upload files ---
uploaded_files = st.file_uploader(
    "Drag and drop your .las or .laz files",
    type=["las", "laz"],
    accept_multiple_files=True
)

st.sidebar.header("Noise Filter Parameters")

# --- PDAL Noise filter parameters with defaults ---
mean_k = st.sidebar.number_input("Mean K (neighbors)", min_value=1, value=8)
multiplier = st.sidebar.number_input("Multiplier", min_value=0.1, value=2.5)
method = st.sidebar.selectbox("Method", ["statistical", "radius"], index=0)

if uploaded_files:
    st.write("### Uploaded Files")
    for file in uploaded_files:
        st.write(f"- {file.name}")

    if st.button("Run Noise Filter"):
        output_files = []

        for file in uploaded_files:
            # Create temp input
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.name)[1]) as tmp_in:
                tmp_in.write(file.read())
                tmp_in.flush()
                input_path = tmp_in.name

            # Output file path
            base, ext = os.path.splitext(file.name)
            output_name = f"{base}_denoise{ext}"
            output_path = os.path.join(tempfile.gettempdir(), output_name)

            # PDAL pipeline
            pipeline_json = {
                "pipeline": [
                    input_path,
                    {
                        "type": "filters.outlier",
                        "method": method,
                        "mean_k": mean_k,
                        "multiplier": multiplier
                    },
                    output_path
                ]
            }

            pipeline = pdal.Pipeline(json.dumps(pipeline_json))
            pipeline.execute()

            output_files.append((output_name, output_path))

        st.success("✅ Noise filtering complete!")

        # --- Individual downloads ---
        st.write("### Download Processed Files")
        for name, path in output_files:
            with open(path, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {name}",
                    data=f,
                    file_name=name,
                    mime="application/octet-stream"
                )

        # --- ZIP all processed files ---
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for name, path in output_files:
                zipf.write(path, arcname=name)
        zip_buffer.seek(0)

        st.download_button(
            label="⬇️ Download All as ZIP",
            data=zip_buffer,
            file_name="denoised_pointclouds.zip",
            mime="application/zip"
        )
