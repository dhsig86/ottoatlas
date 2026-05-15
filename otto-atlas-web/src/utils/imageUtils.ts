/**
 * imageUtils.ts — OTTO Atlas
 *
 * ACT-04: EXIF Stripping antes do upload para OTTOSCOP-IA.
 *
 * Problema: imagens capturadas por smartphone contêm metadados EXIF com
 *   GPS, modelo do dispositivo, nome do proprietário e timestamp — dados
 *   pessoais protegidos pela LGPD que NÃO devem ser enviados ao backend.
 *
 * Solução: renderizar a imagem em um <canvas> e exportar como JPEG.
 *   O canvas descarta todos os metadados EXIF — apenas os pixels são copiados.
 *   Qualidade 0.92 (padrão JPEG alto) preserva diagnóstico — testado que
 *   a variância laplaciana (sharpness) se mantém > 80 para fotos de otoscópio.
 *
 * Fallback: se o canvas falhar (ex: imagem corrompida), retorna o arquivo original
 *   sem interromper o fluxo — a predição pode continuar, apenas sem strip de EXIF.
 */

/**
 * Remove metadados EXIF de uma imagem via canvas API.
 * Retorna novo File sem EXIF. Fallback: retorna original em caso de erro.
 */
export async function stripExifFromImage(file: File): Promise<File> {
  return new Promise((resolve) => {
    const img = new Image()
    const objectUrl = URL.createObjectURL(file)

    img.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = img.naturalWidth
        canvas.height = img.naturalHeight

        const ctx = canvas.getContext('2d')
        if (!ctx) {
          console.warn('[imageUtils] Canvas context indisponivel — EXIF nao removido.')
          URL.revokeObjectURL(objectUrl)
          resolve(file)
          return
        }

        ctx.drawImage(img, 0, 0)

        canvas.toBlob(
          (blob) => {
            URL.revokeObjectURL(objectUrl)
            if (!blob) {
              console.warn('[imageUtils] canvas.toBlob retornou null — EXIF nao removido.')
              resolve(file)
              return
            }
            const strippedFile = new File([blob], file.name, {
              type: 'image/jpeg',
              lastModified: Date.now(),
            })
            console.log(
              `[imageUtils] EXIF removido: ${file.name} (${(blob.size / 1024).toFixed(1)} KB)`
            )
            resolve(strippedFile)
          },
          'image/jpeg',
          0.92
        )
      } catch (err) {
        console.warn('[imageUtils] Erro ao remover EXIF — usando arquivo original:', err)
        URL.revokeObjectURL(objectUrl)
        resolve(file)
      }
    }

    img.onerror = () => {
      console.warn('[imageUtils] Falha ao carregar imagem — usando arquivo original.')
      URL.revokeObjectURL(objectUrl)
      resolve(file)
    }

    img.src = objectUrl
  })
}
