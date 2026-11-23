package com.autoclip.ai

import android.content.Intent
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.animation.AnimatedVisibility
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.VerticalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Share
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.autoclip.ai.data.api.AutoClipApi
import com.autoclip.ai.data.model.ClipInfo
import com.autoclip.ai.data.model.ClipSubmitRequest
import com.autoclip.ai.ui.player.VerticalClipPlayer
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme(
                colorScheme = darkColorScheme(
                    primary = Color(0xFF9333EA),
                    background = Color(0xFF0B0F19),
                    surface = Color(0xFF1E293B)
                )
            ) {
                AutoClipMainScreen()
            }
        }
    }
}

@Composable
fun AutoClipMainScreen() {
    val context = LocalContext.current
    val coroutineScope = rememberCoroutineScope()

    var serverUrl by remember { mutableStateOf("http://192.168.1.100:8000") }
    var api by remember(serverUrl) { mutableStateOf(AutoClipApi.create(serverUrl)) }

    var vodUrlInput by remember { mutableStateOf("") }
    var showDialog by remember { mutableStateOf(false) }
    var isProcessing by remember { mutableStateOf(false) }
    var progressPercent by remember { mutableStateOf(0) }
    var currentStepText by remember { mutableStateOf("Ready") }
    var clips by remember { mutableStateOf<List<ClipInfo>>(emptyList()) }

    fun startPolling(jobId: String) {
        coroutineScope.launch {
            isProcessing = true
            while (isProcessing) {
                try {
                    val status = api.getJobStatus(jobId)
                    progressPercent = status.progressPercent
                    currentStepText = status.currentStep

                    if (status.status == "COMPLETED") {
                        clips = status.clips
                        isProcessing = false
                    } else if (status.status == "FAILED") {
                        isProcessing = false
                    }
                } catch (e: Exception) {
                    currentStepText = "Connecting: ${e.localizedMessage}"
                }
                delay(1500)
            }
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(Color(0xFF0B0F19))) {
        when {
            isProcessing -> {
                // Processing Screen
                Column(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    CircularProgressIndicator(
                        progress = { progressPercent / 100f },
                        modifier = Modifier.size(96.dp),
                        color = Color(0xFFC084FC),
                        strokeWidth = 6.dp
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                    Text(
                        text = "$progressPercent%",
                        fontSize = 28.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = currentStepText,
                        fontSize = 14.sp,
                        color = Color(0xFFCBD5E1)
                    )
                }
            }
            clips.isNotEmpty() -> {
                // Vertical Clips Feed (TikTok / Reels Style)
                val pagerState = rememberPagerState(pageCount = { clips.size })
                VerticalPager(
                    state = pagerState,
                    modifier = Modifier.fillMaxSize()
                ) { page ->
                    val clip = clips[page]
                    // Prepend server base URL if relative path
                    val absoluteVideoUrl = if (clip.videoUrl.startsWith("http")) {
                        clip.videoUrl
                    } else {
                        "$serverUrl${clip.videoUrl}"
                    }

                    Box(modifier = Modifier.fillMaxSize()) {
                        VerticalClipPlayer(
                            videoUrl = absoluteVideoUrl,
                            isPlaying = pagerState.currentPage == page
                        )

                        // Dark Gradient Overlay for text readability
                        Box(
                            modifier = Modifier
                                .fillMaxSize()
                                .background(
                                    Brush.verticalGradient(
                                        listOf(
                                            Color.Transparent,
                                            Color.Transparent,
                                            Color.Black.copy(alpha = 0.85f)
                                        )
                                    )
                                )
                        )

                        // Bottom Metadata
                        Column(
                            modifier = Modifier
                                .align(Alignment.BottomStart)
                                .padding(start = 16.dp, bottom = 32.dp, end = 80.dp)
                        ) {
                            Surface(
                                shape = RoundedCornerShape(12.dp),
                                color = Color(0xFFEC4899).copy(alpha = 0.25f),
                                border = null
                            ) {
                                Text(
                                    text = clip.viralCategory,
                                    color = Color(0xFFF472B6),
                                    fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                                )
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = clip.title,
                                fontSize = 18.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                text = "${clip.duration.toInt()}s • Score: ${clip.score}",
                                fontSize = 12.sp,
                                color = Color(0xFFCBD5E1)
                            )
                        }

                        // Right Floating Share Button
                        FloatingActionButton(
                            onClick = {
                                val shareIntent = Intent(Intent.ACTION_SEND).apply {
                                    type = "text/plain"
                                    putExtra(Intent.EXTRA_SUBJECT, clip.title)
                                    putExtra(Intent.EXTRA_TEXT, "Watch this viral clip: $absoluteVideoUrl")
                                }
                                context.startActivity(Intent.createChooser(shareIntent, "Share Clip via"))
                            },
                            modifier = Modifier
                                .align(Alignment.BottomEnd)
                                .padding(end = 16.dp, bottom = 32.dp),
                            shape = CircleShape,
                            containerColor = Color(0xFF9333EA)
                        ) {
                            Icon(Icons.Default.Share, contentDescription = "Share", tint = Color.White)
                        }
                    }
                }
            }
            else -> {
                // Empty Welcome State
                Column(
                    modifier = Modifier.fillMaxSize().padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = "🎬 AutoClip AI",
                        fontSize = 32.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "Turn Twitch & YouTube streams into viral TikTok/Reels clips instantly.",
                        fontSize = 14.sp,
                        color = Color(0xFF94A3B8),
                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(32.dp))
                    Button(
                        onClick = { showDialog = true },
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF9333EA)),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Icon(Icons.Default.Add, contentDescription = null)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Add VOD Link")
                    }
                }
            }
        }

        // Top Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text("AutoClip", fontWeight = FontWeight.Bold, color = Color.White, fontSize = 20.sp)
            IconButton(onClick = { showDialog = true }) {
                Icon(Icons.Default.Add, contentDescription = "New Job", tint = Color.White)
            }
        }

        // Submit Dialog
        if (showDialog) {
            AlertDialog(
                onDismissRequest = { showDialog = false },
                title = { Text("New AutoClip Job") },
                text = {
                    Column {
                        OutlinedTextField(
                            value = serverUrl,
                            onValueChange = { serverUrl = it },
                            label = { Text("Server Base URL") },
                            modifier = Modifier.fillMaxWidth()
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        OutlinedTextField(
                            value = vodUrlInput,
                            onValueChange = { vodUrlInput = it },
                            label = { Text("Twitch or YouTube URL") },
                            placeholder = { Text("https://...") },
                            modifier = Modifier.fillMaxWidth()
                        )
                    }
                },
                confirmButton = {
                    Button(
                        onClick = {
                            showDialog = false
                            coroutineScope.launch {
                                try {
                                    val req = ClipSubmitRequest(vodUrl = vodUrlInput.trim())
                                    val job = api.submitJob(req)
                                    startPolling(job.jobId)
                                } catch (e: Exception) {
                                    // Handle network error
                                }
                            }
                        }
                    ) {
                        Text("Start Clipping")
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showDialog = false }) {
                        Text("Cancel")
                    }
                }
            )
        }
    }
}
