package com.autoclip.ai.data.api

import com.autoclip.ai.data.model.ClipSubmitRequest
import com.autoclip.ai.data.model.JobStatusResponse
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.Body
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path
import java.util.concurrent.TimeUnit

interface AutoClipApi {
    @POST("/api/v1/jobs/submit")
    suspend fun submitJob(@Body request: ClipSubmitRequest): JobStatusResponse

    @GET("/api/v1/jobs/{job_id}")
    suspend fun getJobStatus(@Path("job_id") jobId: String): JobStatusResponse

    companion object {
        // Change to your PC's local Wi-Fi IP address (e.g., http://192.168.1.100:8000)
        private const val DEFAULT_BASE_URL = "http://10.0.2.2:8000"

        fun create(baseUrl: String = DEFAULT_BASE_URL): AutoClipApi {
            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }
            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(30, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .build()

            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(AutoClipApi::class.java)
        }
    }
}
