<template>
  <el-dialog
    v-model="visible"
    title="上传 Skill"
    width="520px"
    :close-on-click-modal="false"
    @close="resetForm"
  >
    <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item label="名称" prop="name">
        <el-input v-model="form.name" placeholder="输入 Skill 名称" maxlength="50" />
      </el-form-item>
      <el-form-item label="描述" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="输入 Skill 描述"
          maxlength="200"
        />
      </el-form-item>
      <el-form-item label="标签" prop="tags">
        <el-checkbox-group v-model="form.tags">
          <el-checkbox v-for="tag in TAG_OPTIONS" :key="tag" :label="tag" :value="tag">
            {{ tag }}
          </el-checkbox>
        </el-checkbox-group>
      </el-form-item>
      <el-form-item label="文件" prop="file">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          accept=".zip"
          :on-change="onFileChange"
          :on-remove="onFileRemove"
          :file-list="fileList"
        >
          <el-button type="primary" plain>选择 ZIP 文件</el-button>
          <template #tip>
            <div class="el-upload__tip">仅支持 .zip 格式</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="uploading" @click="submitUpload">上传</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, UploadInstance, UploadFile } from 'element-plus'

const TAG_OPTIONS = ['代码开发', 'DSL', '悍马平台', '数据']

const visible = ref(false)
const uploading = ref(false)
const formRef = ref<FormInstance>()
const uploadRef = ref<UploadInstance>()
const fileList = ref<UploadFile[]>([])

const form = reactive({
  name: '',
  description: '',
  tags: [] as string[],
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  description: [{ required: true, message: '请输入描述', trigger: 'blur' }],
  tags: [{ type: 'array', min: 1, message: '至少选择一个标签', trigger: 'change' }],
}

let rawFile: File | null = null

const emit = defineEmits<{
  uploaded: []
}>()

function onFileChange(file: UploadFile) {
  rawFile = file.raw ?? null
  fileList.value = [file]
}

function onFileRemove() {
  rawFile = null
  fileList.value = []
}

function resetForm() {
  formRef.value?.resetFields()
  uploadRef.value?.clearFiles()
  rawFile = null
  fileList.value = []
}

async function submitUpload() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  if (!rawFile) {
    ElMessage.warning('请选择 ZIP 文件')
    return
  }

  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('description', form.description)
    fd.append('tags', form.tags.join(','))
    fd.append('file', rawFile)

    const res = await fetch('/api/skills', { method: 'POST', body: fd })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || '上传失败')
    }
    ElMessage.success('上传成功')
    visible.value = false
    emit('uploaded')
  } catch (e: any) {
    ElMessage.error(e.message || '上传失败')
  } finally {
    uploading.value = false
  }
}

defineExpose({ open: () => { visible.value = true } })
</script>
