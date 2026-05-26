import streamlit as st
import tempfile, os, io
import pandas as pd
from extract import extract_text_from_pdf
from scorer import compute_match_score
from skill_analyzer import analyze_skill_gap

def render():
    st.markdown("## 🏢 HR Recruiter Portal")
    st.markdown("Upload multiple resumes and rank candidates against your job description automatically.")
    st.divider()

    # ── INPUTS ──
    st.subheader("📋 Job Description")
    jd_text = st.text_area("Paste the JD here", height=150, key="hr_jd",
                           placeholder="We are looking for an ML Engineer with Python, PyTorch...")

    st.subheader("📄 Upload Candidate Resumes")
    uploaded_files = st.file_uploader("Upload multiple PDFs", type=["pdf"],
                                      accept_multiple_files=True, key="hr_resumes")

    if uploaded_files:
        st.info(f"📁 {len(uploaded_files)} resume(s) uploaded")

    screen_btn = st.button("🚀 Screen All Candidates", use_container_width=True, type="primary")

    if screen_btn:
        if not uploaded_files:
            st.error("❌ Please upload at least one resume.")
            return
        if not jd_text.strip():
            st.error("❌ Please paste a job description.")
            return

        results_list = []
        progress = st.progress(0, text="🔍 Screening candidates...")

        # Save JD once
        jd_tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".txt", mode='w', encoding='utf-8')
        jd_tmp.write(jd_text)
        jd_tmp.close()

        for i, resume_file in enumerate(uploaded_files):
            progress.progress(
                int((i / len(uploaded_files)) * 100),
                text=f"🔍 Screening {resume_file.name} ({i+1}/{len(uploaded_files)})..."
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(resume_file.read())
                tmp_path = tmp.name

            try:
                resume_text  = extract_text_from_pdf(tmp_path)
                overall_score = compute_match_score(tmp_path, jd_tmp.name)
                gap          = analyze_skill_gap(resume_text, jd_text)
                skill_pct    = round(len(gap["matched"]) / max(len(gap["jd_required"]), 1) * 100, 1)

                results_list.append({
                    "Candidate":       resume_file.name.replace(".pdf", ""),
                    "Overall Match %": overall_score,
                    "Skill Match %":   skill_pct,
                    "Skills Matched":  len(gap["matched"]),
                    "Skills Missing":  len(gap["missing"]),
                    "Matched Skills":  ", ".join(gap["matched"]),
                    "Missing Skills":  ", ".join(gap["missing"]),
                    "Verdict": "✅ Shortlist" if overall_score >= 65
                               else "🟡 Maybe" if overall_score >= 45
                               else "❌ Reject"
                })
            except Exception as e:
                results_list.append({
                    "Candidate": resume_file.name,
                    "Overall Match %": 0,
                    "Skill Match %": 0,
                    "Skills Matched": 0,
                    "Skills Missing": 0,
                    "Matched Skills": "",
                    "Missing Skills": "",
                    "Verdict": f"⚠️ Error: {e}"
                })
            finally:
                os.unlink(tmp_path)

        os.unlink(jd_tmp.name)
        progress.progress(100, text="✅ Screening complete!")
        progress.empty()

        # ── RESULTS ──
        df = pd.DataFrame(results_list).sort_values(
            "Overall Match %", ascending=False
        ).reset_index(drop=True)
        df.index += 1  # rank from 1

        st.markdown("---")
        st.markdown("## 🏆 Candidate Rankings")

        total = len(df)

        # ── SMART RELATIVE SHORTLISTING ──
        # Always shortlist top candidates relative to pool size
        # even if scores are low — because hiring must go on
        if total == 1:
            top_n = 1
        elif total <= 3:
            top_n = 1                        # top 1 of 2-3
        elif total <= 6:
            top_n = max(2, round(total * 0.5))   # top 50%
        elif total <= 15:
            top_n = max(3, round(total * 0.4))   # top 40%
        else:
            top_n = max(5, round(total * 0.3))   # top 30%

        # Assign verdict based on relative rank, not absolute score
        def assign_verdict(rank, score):
            if rank <= top_n:
                if score >= 65:
                    return "✅ Shortlist"
                else:
                    return "✅ Shortlist (Best Available)"
            elif rank <= top_n * 2:
                return "⏳ Waitlist"
            else:
                return "❌ Reject"

        df["Verdict"] = [
            assign_verdict(rank, row["Overall Match %"])
            for rank, (_, row) in enumerate(df.iterrows(), start=1)
        ]

        # ── TOP CANDIDATE HIGHLIGHT ──
        top = df.iloc[0]
        score_context = (
            f"{top['Overall Match %']}% match"
            if top["Overall Match %"] >= 60
            else f"{top['Overall Match %']}% match (best in current pool)"
        )
        st.success(
            f"🥇 **Top Candidate: {top['Candidate']}** — {score_context} "
            f"| {top['Skill Match %']}% skill coverage"
        )

        # ── POOL QUALITY WARNING ──
        avg_score = round(df["Overall Match %"].mean(), 1)
        if avg_score < 45:
            st.warning(
                f"⚠️ **Weak Applicant Pool** — Average match is only {avg_score}%. "
                f"Top {top_n} candidate(s) shortlisted based on relative ranking. "
                f"Consider widening the job posting or relaxing requirements."
            )
        elif avg_score < 60:
            st.info(
                f"ℹ️ **Moderate Pool** — Average match: {avg_score}%. "
                f"Top {top_n} shortlisted. Some skill gaps expected."
            )
        else:
            st.success(f"✅ **Strong Pool** — Average match: {avg_score}%. Top {top_n} shortlisted.")

        # ── SUMMARY METRICS ──
        shortlisted_df = df[df["Verdict"].str.startswith("✅")]
        waitlist_df     = df[df["Verdict"].str.startswith("⏳")]
        rejected_df    = df[df["Verdict"].str.startswith("❌")]

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("👥 Total Screened", total)
        col2.metric("✅ Shortlisted",    len(shortlisted_df))
        col3.metric("⏳ Waitlist",        len(waitlist_df))
        col4.metric("❌ Rejected",       len(rejected_df))

        st.divider()

        # ── RANKING TABLE ──
        st.markdown("### 📊 Full Ranking Table")

        # Color verdicts in table
        def color_verdict(val):
            if val.startswith("✅"):
                return "color: #2ecc71; font-weight: bold"
            elif val.startswith("⏳"):
                return "color: #f39c12; font-weight: bold"
            else:
                return "color: #e74c3c; font-weight: bold"

        styled_df = df[[
            "Candidate", "Overall Match %", "Skill Match %",
            "Skills Matched", "Skills Missing", "Verdict"
        ]].style.applymap(color_verdict, subset=["Verdict"])

        st.dataframe(styled_df, use_container_width=True, height=300)

        st.divider()

        # ── DETAILED CANDIDATE CARDS ──
        st.markdown("### 🔍 Detailed Candidate Profiles")

        # Show shortlisted first, then waitlist, then rejected
        ordered_df = pd.concat([shortlisted_df, waitlist_df, rejected_df])

        for rank, (_, row) in enumerate(ordered_df.iterrows(), start=1):
            verdict_color = (
                "#2ecc71" if row["Verdict"].startswith("✅") else
                "#f39c12" if row["Verdict"].startswith("⏳") else
                "#e74c3c"
            )
            with st.expander(
                f"#{rank} {row['Verdict']}  {row['Candidate']} — {row['Overall Match %']}%"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("Overall Match", f"{row['Overall Match %']}%")
                c2.metric("Skill Match",   f"{row['Skill Match %']}%")
                c3.metric("Status",        row["Verdict"].split(" ")[0])

                if row["Matched Skills"]:
                    st.markdown("**✅ Has:**")
                    st.markdown("".join([
                        f"<span style='background:#1a3a1a;border:1px solid #2ecc71;"
                        f"border-radius:6px;padding:4px 10px;margin:3px;"
                        f"display:inline-block;color:#2ecc71;font-size:13px'>✅ {s.strip()}</span>"
                        for s in row["Matched Skills"].split(",") if s.strip()
                    ]), unsafe_allow_html=True)

                if row["Missing Skills"]:
                    st.markdown("**❌ Missing:**")
                    st.markdown("".join([
                        f"<span style='background:#3a1a1a;border:1px solid #e74c3c;"
                        f"border-radius:6px;padding:4px 10px;margin:3px;"
                        f"display:inline-block;color:#e74c3c;font-size:13px'>❌ {s.strip()}</span>"
                        for s in row["Missing Skills"].split(",") if s.strip()
                    ]), unsafe_allow_html=True)

                # Hiring note for weak pool shortlists
                if "Best Available" in row["Verdict"]:
                    st.info(
                        "ℹ️ Shortlisted as best available in current pool. "
                        "Score is below ideal — consider additional screening round."
                    )

        st.divider()

        # ── CSV EXPORT ──
        st.markdown("### 📥 Export Results")
        csv = df.to_csv(index=True).encode("utf-8")
        st.download_button(
            label="⬇️ Download Full Report (CSV)",
            data=csv,
            file_name="candidate_screening_report.csv",
            mime="text/csv",
            use_container_width=True
        )