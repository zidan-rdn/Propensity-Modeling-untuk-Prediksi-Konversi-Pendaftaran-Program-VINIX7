
import { useEffect, useState } from 'react'
import './App.css'

const API = 'http://127.0.0.1:8000'

const PAGE_NAMES = [
  'Dashboard',
  'Data Responden',
  'Analisis Data',
  'Prediksi Konversi',
]

function App() {
  const [page, setPage] = useState('Dashboard')
  const [dashboard, setDashboard] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [respondents, setRespondents] = useState([])
  const [tableTotal, setTableTotal] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('')
  const [semesterFilter, setSemesterFilter] = useState('')
  const [motivasiFilter, setMotivasiFilter] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  
const [form, setForm] = useState({
  perguruan_tinggi: '',
  program_studi: '',
  semester: '',
  ipk: '',
  motivasi: '',
  tempat_magang: '',
})

  const [prediction, setPrediction] = useState(null)
  const [predictLoading, setPredictLoading] = useState(false)
  const [predictError, setPredictError] = useState('')

  // =====================================
  // MEMUAT DASHBOARD
  // =====================================

  useEffect(() => {
    fetch(`${API}/dashboard`)
      .then((res) => {
        if (!res.ok) throw new Error('Gagal mengambil dashboard')
        return res.json()
      })
      .then(setDashboard)
      .catch((err) => setError(err.message))

    fetch(`${API}/analytics`)
      .then((res) => {
        if (!res.ok) throw new Error('Gagal mengambil analisis')
        return res.json()
      })
      .then(setAnalytics)
      .catch((err) => setError(err.message))
  }, [])

  // =====================================
  // MEMUAT DATA RESPONDEN
  // =====================================

  useEffect(() => {
    if (page !== 'Data Responden') return

    const params = new URLSearchParams({
      search,
      status,
      semester: semesterFilter,
      motivasi: motivasiFilter,
      page: String(currentPage),
      limit: '5',
    })

    setLoading(true)

    fetch(`${API}/respondents?${params}`)
      .then((res) => {
        if (!res.ok) throw new Error('Gagal mengambil data responden')
        return res.json()
      })
      .then((data) => {
  console.log('DATA RESPONDEN API:', data.data)
  console.log('RESPONDEN PERTAMA:', data.data?.[0])

  setRespondents(data.data)
  setTableTotal(data.total)
})
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [
    page,
    search,
    status,
    semesterFilter,
    motivasiFilter,
    currentPage,
  ])

  // =====================================
  // PREDIKSI
  // =====================================


const handlePredict = async (e) => {
  e.preventDefault()

  setPredictLoading(true)
  setPrediction(null)
  setPredictError('')

  try {
    const response = await fetch(`${API}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        perguruan_tinggi: form.perguruan_tinggi.trim(),
        program_studi: form.program_studi.trim(),
        semester: Number(form.semester),
        ipk: Number(form.ipk),
        motivasi: form.motivasi,
        tempat_magang: form.tempat_magang.trim(),
      }),
    })

    const data = await response.json()

    if (!response.ok) {
      const detail = data.detail
      const message = Array.isArray(detail)
        ? detail.map((item) => item.msg).join(', ')
        : typeof detail === 'string'
          ? detail
          : 'Prediksi gagal. Periksa kembali data input.'

      throw new Error(message)
    }

    setPrediction(data.hasil_prediksi)

  } catch (err) {
    setPredictError(err.message)
  } finally {
    setPredictLoading(false)
  }
}
  const handleFormChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    })
  }

  const resetFilters = () => {
    setSearch('')
    setStatus('')
    setSemesterFilter('')
    setMotivasiFilter('')
    setCurrentPage(1)
  }

  const exportData = () => {
    window.open(`${API}/export`, '_blank')
  }

  return (
    <div className="app-shell">

      {/* NAVBAR */}

      <header className="navbar">
        <div className="brand">
          VINIX<span>7</span>
        </div>

        <nav className="nav-menu">
          {PAGE_NAMES.map((name) => (
            <button
              key={name}
              className={`nav-link ${page === name ? 'active' : ''}`}
              onClick={() => setPage(name)}
            >
              {name}
            </button>
          ))}
        </nav>

      </header>

      <main className="main-content">

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {/* =====================================
            HALAMAN DASHBOARD
        ===================================== */}

        {page === 'Dashboard' && (
          <section>

            <div className="hero-section">
              <div className="hero-content">

                <h1>
                  Prediksi Konversi
                  <br />
                  Pendaftaran Program
                  <br />
                  <span>VINIX7</span>
                </h1>

                <p>
                  Prediksi kesediaan calon
                  peserta mengikuti program VINIX7 menggunakan
                  teknologi Machine Learning.
                </p>

                <button
                  className="primary-button"
                  onClick={() => setPage('Analisis Data')}
                >
                  Jelajahi →
                </button>
              </div>

              <div className="hero-visual">
                <div className="visual-icon">📊</div>
                <div className="visual-caption">
                  VINIX7 Analytics
                </div>
              </div>
            </div>

            <div className="stats-grid">

              <StatCard
                icon="👥"
                title="Total Responden"
                value={
                  dashboard
                    ? dashboard.total_responden.toLocaleString('id-ID')
                    : '...'
                }
                description="Data responden resmi"
              />

              <StatCard
                icon="◎"
                title="Rata-rata Total Score"
                value={
                  dashboard
                    ? dashboard.rata_rata_score
                    : '...'
                }
                description="Rata-rata skor responden"
              />

              <StatCard
                icon="↗"
                title="Akurasi Model"
                value={
                  dashboard
                    ? `${dashboard.akurasi_model}%`
                    : '...'
                }
                description="Evaluasi data pengujian"
              />

            </div>

          </section>
        )}

        {/* =====================================
            HALAMAN DATA RESPONDEN
        ===================================== */}

        {page === 'Data Responden' && (
          <section>

            <div className="page-heading">
              <div>
                <h1>Data Responden</h1>
                <p>
                  Informasi responden berdasarkan dataset asli.
                </p>
              </div>

            </div>

            <div className="panel">
              
<div className="table-wrapper">
  <table>
    <thead>
      <tr>
        <th>No.</th>
        <th>Perguruan Tinggi</th>
        <th>Program Studi</th>
        <th>Semester</th>
        <th>IPK</th>
        <th>Dream Job</th>
        <th>Total Score</th>
        <th>Motivasi</th>
        <th>Kesediaan</th>
        <th>Archetype</th>

        <th>M1 Background</th>
        <th>M2 Skills</th>
        <th>M3 Industry</th>
        <th>M4 Interest</th>
        <th>M5 Compass</th>
        <th>M6 Company</th>
        <th>M7 Branding</th>
        <th>M8 Ambisi</th>
        <th>M9 Resiliensi</th>

        <th>Jalur Karir</th>
        <th>Bidang Minat</th>
        <th>Work Values</th>
        <th>Work Style</th>
        <th>Cognitive Style</th>
        <th>Ukuran Perusahaan</th>
        <th>Kultur Kerja</th>
        <th>Preferensi Lokasi</th>
        <th>Ekspektasi Gaji</th>
        <th>Minat Wirausaha</th>
        <th>Rencana S2/Sertifikasi</th>
        <th>Frekuensi Belajar</th>
        <th>Kesiapan Interview</th>
        <th>Level Bahasa Inggris</th>
        <th>Verdict Kesiapan</th>
        <th>Rekomendasi Industri 1</th>
        <th>Rekomendasi Industri 2</th>
      </tr>
    </thead>

    <tbody>
      {loading ? (
        <tr>
          <td colSpan="36" className="empty-state">
            Memuat data...
          </td>
        </tr>
      ) : respondents.length === 0 ? (
        <tr>
          <td colSpan="36" className="empty-state">
            Data tidak ditemukan.
          </td>
        </tr>
      ) : (
        respondents.map((item, index) => (
          <tr key={`${currentPage}-${index}`}>
            <td>{(currentPage - 1) * 5 + index + 1}</td>
            <td>{item['Perguruan Tinggi'] ?? '-'}</td>
            <td>{item['Program Studi'] ?? '-'}</td>
            <td>{item.Semester ?? '-'}</td>
            <td>{item.IPK ?? '-'}</td>
            <td>{item['Dream Job'] ?? '-'}</td>
            <td>{item['Total Score'] ?? '-'}</td>
            <td>{item.Motivasi ?? '-'}</td>

            <td>
              <span
                className={`status-badge ${
                  String(item['Ikut Program VINIX7?'])
                    .toLowerCase().trim() === 'ya'
                    ? 'yes'
                    : 'no'
                }`}
              >
                {item['Ikut Program VINIX7?'] ?? '-'}
              </span>
            </td>

            <td>{item.Archetype ?? '-'}</td>

            <td>{item['Skor M1 (Background)'] ?? '-'}</td>
            <td>{item['Skor M2 (Skills)'] ?? '-'}</td>
            <td>{item['Skor M3 (Industry)'] ?? '-'}</td>
            <td>{item['Skor M4 (Interest)'] ?? '-'}</td>
            <td>{item['Skor M5 (Compass)'] ?? '-'}</td>
            <td>{item['Skor M6 (Company)'] ?? '-'}</td>
            <td>{item['Skor M7 (Branding)'] ?? '-'}</td>
            <td>{item['Skor M8 (Ambisi)'] ?? '-'}</td>
            <td>{item['Skor M9 (Resiliensi)'] ?? '-'}</td>

            <td>{item['Jalur Karir'] ?? '-'}</td>
            <td>{item['Bidang Minat'] ?? '-'}</td>
            <td>{item['Work Values'] ?? '-'}</td>
            <td>{item['Work Style'] ?? '-'}</td>
            <td>{item['Cognitive Style'] ?? '-'}</td>
            <td>{item['Ukuran Perusahaan'] ?? '-'}</td>
            <td>{item['Kultur Kerja'] ?? '-'}</td>
            <td>{item['Preferensi Lokasi'] ?? '-'}</td>
            <td>{item['Ekspektasi Gaji'] ?? '-'}</td>
            <td>{item['Minat Wirausaha'] ?? '-'}</td>
            <td>{item['Rencana S2/Sertifikasi'] ?? '-'}</td>
            <td>{item['Frekuensi Belajar'] ?? '-'}</td>
            <td>{item['Kesiapan Interview'] ?? '-'}</td>
            <td>{item['Level Bahasa Inggris'] ?? '-'}</td>
            <td>{item['Verdict Kesiapan'] ?? '-'}</td>
            <td>{item['Rekomendasi Industri 1'] ?? '-'}</td>
            <td>{item['Rekomendasi Industri 2'] ?? '-'}</td>
          </tr>
        ))
      )}
    </tbody>
  </table>
</div>

              <div className="pagination">
                <span>
                  Total {tableTotal.toLocaleString('id-ID')} responden
                </span>

                <div>
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => setCurrentPage((p) => p - 1)}
                  >
                    ←
                  </button>

                  <span>Halaman {currentPage}</span>

                  <button
                    disabled={currentPage * 10 >= tableTotal}
                    onClick={() => setCurrentPage((p) => p + 1)}
                  >
                    →
                  </button>
                </div>
              </div>

            </div>
          </section>
        )}

        {/* =====================================
            HALAMAN ANALISIS DATA
        ===================================== */}

        {page === 'Analisis Data' && (
          <section>

            <div className="page-heading">
              <div>
                <h1>Analisis Data</h1>
                <p>
                  Visualisasi dan analisis berdasarkan 2.988 responden.
                </p>
              </div>
            </div>

            {!analytics ? (
              <div className="panel">Memuat analisis data...</div>
            ) : (
              <>
                
<div className="content-grid">

  <div className="panel">
    <PanelTitle title="Distribusi Status Kesiapan"
      subtitle="Kategori kesiapan responden" />
    <BarList data={analytics.distribusi_kesiapan} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Kesediaan"
      subtitle="Kesediaan mengikuti program VINIX7" />
    <BarList data={analytics.distribusi_kesediaan} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Archetype"
      subtitle="Karakteristik archetype responden" />
    <BarList data={analytics.distribusi_archetype} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Perguruan Tinggi"
      subtitle="Asal perguruan tinggi responden" />
    <BarList data={analytics.distribusi_perguruan_tinggi} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Program Studi"
      subtitle="Program studi responden" />
    <BarList data={analytics.distribusi_program_studi} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Semester"
      subtitle="Semester responden" />
    <BarList data={analytics.distribusi_semester} />
  </div>

  
{[
  ['M1 Background', analytics.distribusi_m1],
  ['M2 Skills', analytics.distribusi_m2],
  ['M3 Industry', analytics.distribusi_m3],
  ['M4 Interest', analytics.distribusi_m4],
  ['M5 Compass', analytics.distribusi_m5],
  ['M6 Company', analytics.distribusi_m6],
  ['M7 Branding', analytics.distribusi_m7],
  ['M8 Ambisi', analytics.distribusi_m8],
  ['M9 Resiliensi', analytics.distribusi_m9],
].map(([title, data]) => (
  <div className="panel" key={title}>
    <PanelTitle
      title={title}
      subtitle="Distribusi skor responden VINIX7"
    />
    <BarList data={data || []} />
  </div>
))}

  <div className="panel">
    <PanelTitle title="Distribusi Jalur Karir"
      subtitle="Pilihan jalur karir responden" />
    <BarList data={analytics.distribusi_jalur_karir} />
  </div>

  <div className="panel">
    <PanelTitle title="Distribusi Bidang Minat"
      subtitle="Bidang yang diminati responden" />
    <BarList data={analytics.distribusi_bidang_minat} />
  </div>

  <div className="panel">
    <PanelTitle title="Work Values"
      subtitle="Nilai yang diprioritaskan responden" />
    <BarList data={analytics.distribusi_work_values} />
  </div>

  <div className="panel">
    <PanelTitle title="Work Style"
      subtitle="Preferensi gaya bekerja" />
    <BarList data={analytics.distribusi_work_style} />
  </div>

  <div className="panel">
    <PanelTitle title="Cognitive Style"
      subtitle="Gaya berpikir responden" />
    <BarList data={analytics.distribusi_cognitive_style} />
  </div>

<div className="panel">
  <PanelTitle
    title="Preferensi Perusahaan"
    subtitle="Ukuran perusahaan dan kultur kerja"
  />

  <div className="analysis-group">
    <h4>Ukuran Perusahaan</h4>
    <BarList data={analytics.distribusi_ukuran_perusahaan} />
  </div>

  <div className="analysis-group">
    <h4>Kultur Kerja</h4>
    <BarList data={analytics.distribusi_kultur_kerja} />
  </div>
</div>

<div className="panel">
  <PanelTitle
    title="Preferensi Pekerjaan"
    subtitle="Lokasi dan ekspektasi gaji"
  />

  <div className="analysis-group">
    <h4>Preferensi Lokasi</h4>
    <BarList data={analytics.distribusi_lokasi} />
  </div>

  <div className="analysis-group">
    <h4>Ekspektasi Gaji</h4>
    <BarList data={analytics.distribusi_gaji} />
  </div>
</div>

  <div className="panel">
    <PanelTitle title="Minat Wirausaha"
      subtitle="Ketertarikan responden terhadap kewirausahaan" />
    <BarList data={analytics.distribusi_wirausaha} />
  </div>

  <div className="panel">
    <PanelTitle title="Pengembangan Diri"
      subtitle="Rencana pendidikan dan kebiasaan belajar" />
    <h4>Rencana S2/Sertifikasi</h4>
    <BarList data={analytics.distribusi_rencana} />
    <h4>Frekuensi Belajar</h4>
    <BarList data={analytics.distribusi_frekuensi_belajar} />
  </div>

  <div className="panel">
    <PanelTitle title="Kesiapan Profesional"
      subtitle="Kesiapan interview dan kemampuan bahasa Inggris" />
    <h4>Kesiapan Interview</h4>
    <BarList data={analytics.distribusi_interview} />
    <h4>Level Bahasa Inggris</h4>
    <BarList data={analytics.distribusi_bahasa_inggris} />
  </div>

  <div className="panel">
    <PanelTitle title="Rekomendasi Industri"
      subtitle="Distribusi rekomendasi industri VINIX7" />
    <h4>Rekomendasi Industri 1</h4>
    <BarList data={analytics.distribusi_industri_1} />
    <h4>Rekomendasi Industri 2</h4>
    <BarList data={analytics.distribusi_industri_2} />
  </div>

</div>

              </>
            )}
          </section>
        )}

        {/* =====================================
            HALAMAN PREDIKSI
        ===================================== */}

        {page === 'Prediksi Konversi' && (
          <section>

            <div className="prediction-layout">

              <div className="panel">
                <PanelTitle
                  title="Input Data Calon Peserta"
                />

                <form onSubmit={handlePredict}>
                  <FormField label="Perguruan Tinggi">
                    <input
                      type="text"
                      name="perguruan_tinggi"
                      value={form.perguruan_tinggi}
                      onChange={handleFormChange}
                      placeholder="Masukkan nama perguruan tinggi"
                      required
                    />
                  </FormField>

                  <FormField label="Program Studi">
                    <input
                      type="text"
                      name="program_studi"
                      value={form.program_studi}
                      onChange={handleFormChange}
                      placeholder="Masukkan nama program studi"
                      required
                    />
                  </FormField>

                  
<FormField label="Semester">
  <select
    name="semester"
    value={form.semester}
    onChange={handleFormChange}
    required
  >
    <option value="" disabled>
      Pilih Semester
    </option>

    {[1, 2, 3, 4, 5, 6, 7, 8].map((v) => (
      <option key={v} value={v}>
        Semester {v}
      </option>
    ))}
  </select>
</FormField>

                  <FormField label="IPK">
  <input
    type="number"
    name="ipk"
    value={form.ipk}
    onChange={handleFormChange}
    min="0"
    max="4"
    step="0.01"
    placeholder="Masukkan IPK (contoh: 3.50)"
    required
  />
</FormField>


<FormField label="Motivasi">
  <select
    name="motivasi"
    value={form.motivasi}
    onChange={handleFormChange}
    required
  >
    <option value="">Pilih Motivasi</option>
    {['money', 'growth', 'impact', 'prestige', 'freedom'].map((v) => (
      <option key={v} value={v}>
        {v.charAt(0).toUpperCase() + v.slice(1)}
      </option>
    ))}
  </select>
</FormField>


<FormField label="Tempat Magang">
  <input
    type="text"
    name="tempat_magang"
    value={form.tempat_magang}
    onChange={handleFormChange}
    placeholder="Masukkan nama tempat magang"
    required
  />
</FormField>

                  <button
                    type="submit"
                    className="primary-button full-button"
                    disabled={predictLoading}
                  >
                    {predictLoading
                      ? 'Sedang Memprediksi...'
                      : '✦ Prediksi Sekarang'}
                  </button>
                </form>

                {predictError && (
                  <div className="error-message">
                    {predictError}
                  </div>
                )}
              </div>

              <div className="panel result-panel">
                <PanelTitle
                  title="Hasil Prediksi Ikut Program VINIX7?"
                />

                {!prediction ? (
                  <div className="empty-result">
                    <div>◎</div>
                    <h3>Belum Ada Prediksi</h3>
                    <p>
                      Masukkan informasi calon peserta
                      kemudian klik Prediksi Sekarang.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="score-circle">
                      <strong>
                        {prediction.skor_konversi.toFixed(2)}%
                      </strong>
                    </div>

                    <div className="prediction-status">
                      <h3>
                        Prediksi: {prediction.kesediaan.toUpperCase()}
                      </h3>
                      <p>
                        Berdasarkan pola data yang dipelajari
                        oleh model Logistic Regression.
                      </p>
                    </div>

                    <h3 className="probability-heading">
                      Rincian Probabilitas
                    </h3>

                  </>
                )}

                <p className="disclaimer">
                  Hasil merupakan estimasi probabilitas model,
                  bukan jaminan keputusan aktual seseorang
                  untuk mendaftar program VINIX7.
                </p>
              </div>

            </div>
          </section>
        )}

      </main>

    </div>
  )
}

// =====================================
// KOMPONEN STATISTIK
// =====================================

function StatCard({ icon, title, value, description }) {
  return (
    <div className="stat-card">
      <div className="stat-icon">{icon}</div>
      <p>{title}</p>
      <h2>{value}</h2>
      <small>{description}</small>
    </div>
  )
}

// =====================================
// KOMPONEN JUDUL PANEL
// =====================================

function PanelTitle({ title, subtitle }) {
  return (
    <div className="panel-title">
      <div>
        <h3>{title}</h3>
        <p>{subtitle}</p>
      </div>
    </div>
  )
}

// =====================================
// KOMPONEN GRAFIK BATANG
// =====================================

function BarList({ data = [] }) {
  if (!data.length) {
    return <p>Belum ada data.</p>
  }

  return (
    <div className="bar-list">
      {data.slice(0, 5).map((item) => (
        <div className="bar-item" key={item.label}>
          <div className="bar-label">
            <span>{item.label}</span>
            <strong>{item.persentase}%</strong>
          </div>

          <div className="bar-track">
            <div
              className="bar-fill"
              style={{ width: `${item.persentase}%` }}
            />
          </div>

          <small>
            {item.jumlah.toLocaleString('id-ID')} responden
          </small>
        </div>
      ))}
    </div>
  )
}

// =====================================
// KOMPONEN FORM
// =====================================

function FormField({ label, children }) {
  return (
    <div className="form-field">
      <label>{label}</label>
      {children}
    </div>
  )
}

export default App
