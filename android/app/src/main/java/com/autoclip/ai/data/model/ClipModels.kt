package com.autoclip.ai.data.model

import com.google.gson.annotations.SerializedName

data class ClipSubmitRequest(
    @SerializedName("vod_url") val vodUrl: String,
    @SerializedName("max_clips") val maxClips: Int = 5,
    @SerializedName("vertical") val vertical: Boolean = true,
    @SerializedName("clip_padding") val clipPadding: Float = 15.0f
)

data class ClipInfo(
    @SerializedName("id") val id: String,
    @SerializedName("job_id") val jobId: String,
    @SerializedName("title") val title: String,
    @SerializedName("start_time") val startTime: Float,
    @SerializedName("end_time") val endTime: Float,
    @SerializedName("duration") val duration: Float,
    @SerializedName("score") val score: Float,
    @SerializedName("dominant_signal") val dominantSignal: String,
    @SerializedName("viral_category") val viralCategory: String,
    @SerializedName("video_url") val videoUrl: String,
    @SerializedName("thumbnail_url") val thumbnailUrl: String?,
    @SerializedName("is_vertical") val isVertical: Boolean
)

data class JobStatusResponse(
    @SerializedName("job_id") val jobId: String,
    @SerializedName("vod_url") val vodUrl: String,
    @SerializedName("status") val status: String,
    @SerializedName("progress_percent") val progressPercent: Int,
    @SerializedName("current_step") val currentStep: String,
    @SerializedName("error_message") val errorMessage: String?,
    @SerializedName("clips") val clips: List<ClipInfo>
)
